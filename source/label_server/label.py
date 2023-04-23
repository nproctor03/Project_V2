import pickle
import math
import faiss
import numpy as np
import pymongo
import torch
import clip
import torch.nn.functional as F


client = pymongo.MongoClient('localhost', 27017)
db = client.images

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-L/14", device=device, jit=True)


age_labels = ["0-2", "3-9", "10-19", "20-29", "30-39",
              "40-49", "50-59", "60-69", "more than 70"]
gender_labels = ["Male", "Female"]
race_labels = ["White", "Black", "Indian", "East Asian",
               "Southeast Asian", "Middle Eastern", "Latino"]


def sentence_builder(age_labels, gender_labels, race_labels):
    sentence_array = []
    for age in age_labels:
        for race in race_labels:
            for gender in gender_labels:
                sentence = "A photo of a " + \
                    str(age)+" year old "+str(race) + " "+str(gender)+"."
                sentence_array.append(sentence)

    return sentence_array


sentences = sentence_builder(age_labels, gender_labels, race_labels)


# set up for clip only detection method
# clip.tokenize() function to converts each of these into tokenized format that can be processed by CLIP
age_tokens = clip.tokenize(age_labels).to(device)
gender_tokens = clip.tokenize(gender_labels).to(device)
race_tokens = clip.tokenize(race_labels).to(device)
sentence_tokens = clip.tokenize(sentences).to(device)

with torch.no_grad():
    age_label_features = model.encode_text(age_tokens)
    gender_label_features = model.encode_text(gender_tokens)
    race_label_features = model.encode_text(race_tokens)
    sentence_features = model.encode_text(sentence_tokens)

# vi stands for verified images. These are used to perform nearest neighbour search
# on images already in the db.
vi_embeddings = np.empty((0, 768), dtype=np.float32)
vi_index = faiss.IndexFlatL2(768)


def build_verified_images():
    collection = db['image_data']
    index = faiss.IndexFlatL2(768)
    try:
        embeddings = np.empty((0, 768), dtype=np.float32)
        # print("Process has started")
        # count = 0
        # Get every image that has been verified in the db
        for item in collection.find({"requiresVerification": "False"}):
            emb = np.array(item['embedding'])
            embeddings = np.append(embeddings, emb, axis=0)
        # If no verified images have been found. return the default index and embeddings objects.
        # else update the index.
        if embeddings.size == 0:
            return embeddings, index

        index.add(embeddings)
        return embeddings, index
    except Exception as e:
        print(e)
        return ("There was an error building the embeddings list.")


def update_data():
    print("Data is updating")
    global vi_embeddings
    global vi_index
    vi_embeddings, vi_index = build_verified_images()
    print("Ntotal: "+str(vi_index.ntotal))
    # print(len(vi_embeddings))
    # print(vi_index.ntotal)


# Clip only method
def label_method_1(embedding):
    try:
        # convert embedding to numpy array
        emb = np.array(embedding).astype('float32')
        image_features = F.normalize(
            torch.from_numpy(emb), p=2, dim=1).to(device)

        # race_text_features = F.normalize(race_label_features, p=2, dim=1)
        # age_text_features = F.normalize(age_label_features, p=2, dim=1)
        # gender_text_features = F.normalize(gender_label_features, p=2, dim=1)

        race_similarity = (100.0 * image_features @
                           race_label_features.T).softmax(dim=-1)
        age_similarity = (100.0 * image_features @
                          age_label_features.T).softmax(dim=-1)
        gender_similarity = (100.0 * image_features @
                             gender_label_features.T).softmax(dim=-1)

        values_race, indices_race = race_similarity[0].topk(1)
        values_age, indices_age = age_similarity[0].topk(1)
        values_gender, indices_gender = gender_similarity[0].topk(1)

        print(values_race)
        print(values_age)
        print(values_gender)

        age = age_labels[int(indices_age[0])]
        gender = gender_labels[int(indices_gender[0])]
        race = race_labels[int(indices_race[0])]

        labels = [age, gender, race]
        status = "success"
        return status, labels

    except Exception as e:
        print("Exception:" + str(e))
        return "No Label Identified"

# Origional method (dont be wrong)


def label_method_2(image_embedding):
    try:
        # convert embedding to numpy array
        emb = np.array(image_embedding).astype('float32')
        # print(vi_index.ntotal)
        if vi_index.ntotal > 0:
            nearest_neighbour_labels = []
            nearest_neighbour_incorrect_labels = []

            # Get the closest matching image from the database.
            _, I = vi_index.search(emb, 3)
            closest_image_embedding_1 = vi_embeddings[[I[0][0]]].tolist()
            closest_image_embedding_2 = vi_embeddings[[I[0][1]]].tolist()
            closest_image_embedding_3 = vi_embeddings[[I[0][2]]].tolist()

            nearest_neighbour_1 = db.image_data.find(
                {"embedding": closest_image_embedding_1, "requiresVerification": "False"})

            for neighbour in nearest_neighbour_1:
                nearest_neighbour_incorrect_labels += neighbour['incorrect_labels']
                nearest_neighbour_labels += neighbour['verified_labels']

            nearest_neighbour_2 = db.image_data.find(
                {"embedding": closest_image_embedding_2, "requiresVerification": "False"})

            for neighbour in nearest_neighbour_2:
                nearest_neighbour_labels += neighbour['verified_labels']
                nearest_neighbour_incorrect_labels += neighbour['incorrect_labels']

            nearest_neighbour_3 = db.image_data.find(
                {"embedding": closest_image_embedding_3, "requiresVerification": "False"})

            for neighbour in nearest_neighbour_3:
                nearest_neighbour_labels += neighbour['verified_labels']
                nearest_neighbour_incorrect_labels += neighbour['incorrect_labels']

            nearest_neighbour_labels = list(set(nearest_neighbour_labels))
            print("Correct labels: " + str(nearest_neighbour_labels))

            nearest_neighbour_incorrect_labels = list(set(
                nearest_neighbour_incorrect_labels))
            print("Incorrect labels: "+str(nearest_neighbour_incorrect_labels))

        else:
            nearest_neighbour_labels = []
            nearest_neighbour_incorrect_labels = []

        age = get_age_label(emb, nearest_neighbour_incorrect_labels)

        gender = get_gender_label(emb, nearest_neighbour_incorrect_labels)

        race = get_race_label(emb, nearest_neighbour_incorrect_labels)

        labels = [age, gender, race]
        status = "success"
        return status, labels

    except Exception as e:
        print(e)
        status = "Fail"
        message = "There was an error processing your request"
        return status, message


# k nearest neighbours method
def label_method_3(image_embedding):
    try:
        # convert embedding to numpy array
        emb = np.array(image_embedding).astype('float32')
        # print(vi_index.ntotal)

        if vi_index.ntotal > 0:
            N = math.sqrt(vi_index.ntotal)
            N = round(N)

            age = get_age_label_2(emb, N)
            gender = get_gender_label_2(emb, N)
            race = get_race_label_2(emb, N)
        else:
            age = get_age_label(emb, [])
            gender = get_gender_label(emb, [])
            race = get_race_label(emb, [])

        labels = [age, gender, race]
        status = "success"
        return status, labels

    except Exception as e:
        print(e)
        status = "Fail"
        message = "There was an error processing your request"
        return status, message


def label_method_4(embedding):
    try:
        # convert embedding to numpy array
        emb = np.array(embedding).astype('float32')
        image_features = F.normalize(
            torch.from_numpy(emb), p=2, dim=1).to(device)

        sentence_similarity = (100.0 * image_features @
                               sentence_features.T).softmax(dim=-1)

        values, indices = sentence_similarity[0].topk(1)
        closest_sentence = sentences[int(indices[0])]
        print(closest_sentence)
        for i in age_labels:
            if i in closest_sentence:
                age = i

        for i in race_labels:
            if i in closest_sentence:
                race = i

        for i in gender_labels:
            if i in closest_sentence:
                gender = i

        labels = [age, gender, race]
        status = "success"
        return status, labels

    except Exception as e:
        print("Exception:" + str(e))
        return "No Label Identified"


def get_age_label(embedding, nearest_neighbour_incorrect_labels):
    try:
        image_features = F.normalize(
            torch.from_numpy(embedding), p=2, dim=1).to(device)
        text_features = F.normalize(age_label_features, p=2, dim=1)
        # embedding /= embedding.norm(dim=-1, keepdim=True)
        # text_features /= age_label_features.norm(dim=-1, keepdim=True)
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        values, indices = similarity[0].topk(len(age_labels))
        # print(int(indices[0]))
        # print("\nTop predictions:\n")

        # for value, index in zip(values, indices):
        #     print(f"{age_labels[index]:>16s}: {100 * value.item():.2f}%")
        index = 0
        for count in range(len(age_labels)):
            label = age_labels[int(indices[index])]
            # print(label)
            index = index+1
            if label not in nearest_neighbour_incorrect_labels:
                break
        else:
            label = "No Label Identified"
        return label
    except Exception as e:
        print("Exception:" + str(e))
        return "No Label Identified"


def get_race_label(embedding, nearest_neighbour_incorrect_labels):
    try:
        image_features = F.normalize(
            torch.from_numpy(embedding), p=2, dim=1).to(device)
        text_features = F.normalize(race_label_features, p=2, dim=1)
        # embedding /= embedding.norm(dim=-1, keepdim=True)
        # text_features /= age_label_features.norm(dim=-1, keepdim=True)
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        values, indices = similarity[0].topk(len(race_labels))

        # print(int(indices[0]))
        # print("\nTop predictions:\n")

        # for value, index in zip(values, indices):
        #     print(f"{race_labels[index]:>16s}: {100 * value.item():.2f}%")

        index = 0
        for count in range(len(race_labels)):
            label = race_labels[int(indices[index])]
            # print(label)
            index = index+1
            if label not in nearest_neighbour_incorrect_labels:
                break
        else:
            label = "No Label Identified"
        return label
    except Exception as e:
        print("Exception:" + str(e))
        return "No Label Identified"


def get_gender_label(embedding, nearest_neighbour_incorrect_labels):
    try:

        image_features = F.normalize(
            torch.from_numpy(embedding), p=2, dim=1).to(device)
        text_features = F.normalize(gender_label_features, p=2, dim=1)
        # embedding /= embedding.norm(dim=-1, keepdim=True)
        # text_features /= age_label_features.norm(dim=-1, keepdim=True)
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        values, indices = similarity[0].topk(len(gender_labels))

        # print(int(indices[0]))
        # print("\nTop predictions:\n")

        # for value, index in zip(values, indices):
        #     print(f"{gender_labels[index]:>16s}: {100 * value.item():.2f}%")

        index = 0
        for count in range(len(gender_labels)):
            label = gender_labels[int(indices[index])]
            # print(label)
            index = index+1
            if label not in nearest_neighbour_incorrect_labels:
                break
        else:
            label = "No Label Identified"
        return label

    except Exception as e:
        print("Exception:" + str(e))
        return "No Label Identified"


def get_age_label_2(embedding, n):
    try:
        _, I = vi_index.search(embedding, vi_index.ntotal)
        labels_dict = {key: 0 for key in age_labels}

        for index in I[0]:
            nearest_neighbour_embedding = vi_embeddings[index].tolist()
            nearest_neighbour = db.image_data.find(
                {"embedding": nearest_neighbour_embedding, "requiresVerification": "False"})

            closest_labels = []

            for neighbour in nearest_neighbour:
                closest_labels += neighbour['verified_labels']

            for key in labels_dict:
                if key in closest_labels:
                    labels_dict[key] += 1

                if labels_dict[key] == n:
                    return key

        raise ValueError("No label Identified")

    except Exception as e:
        print("Exception:" + str(e))
        return "No Label Identified"


def get_race_label_2(embedding, n):
    try:
        _, I = vi_index.search(embedding, vi_index.ntotal)
        labels_dict = {key: 0 for key in race_labels}

        for index in I[0]:
            nearest_neighbour_embedding = vi_embeddings[index].tolist()
            # nearest_neighbour_embedding = vi_embeddings[index].tolist()

            nearest_neighbour = db.image_data.find(
                {"embedding": nearest_neighbour_embedding, "requiresVerification": "False"})

            closest_labels = []

            for neighbour in nearest_neighbour:
                closest_labels += neighbour['verified_labels']

            for key in labels_dict:
                if key in closest_labels:
                    labels_dict[key] += 1

                if labels_dict[key] == n:
                    return key

        raise ValueError("No label Identified")

    except Exception as e:
        print("Exception:" + str(e))
        return "No Label Identified"


def get_gender_label_2(embedding, n):
    try:
        _, I = vi_index.search(embedding, vi_index.ntotal)
        labels_dict = {key: 0 for key in gender_labels}

        for index in I[0]:
            nearest_neighbour_embedding = vi_embeddings[index].tolist()

            nearest_neighbour = db.image_data.find(
                {"embedding": nearest_neighbour_embedding, "requiresVerification": "False"})

            closest_labels = []

            for neighbour in nearest_neighbour:
                closest_labels += neighbour['verified_labels']

            for key in labels_dict:
                if key in closest_labels:
                    labels_dict[key] += 1

                if labels_dict[key] == n:
                    return key

        raise ValueError("No label Identified")

    except Exception as e:
        print("Exception:" + str(e))
        return "No Label Identified"


# def get__label(embedding, nearest_neighbour_incorrect_labels, index, dictionary):
#     try:
#         D, I = index.search(embedding, int(index.ntotal))

#         # https://www.geeksforgeeks.org/using-else-conditional-statement-with-for-loop-in-python/
#         for count in range(int(index.ntotal)):
#             label = dictionary[I[0][count]]
#             # print(nearest_neighbour_incorrect_labels)

#             if label not in nearest_neighbour_incorrect_labels:
#                 break

#         else:
#             label = "No Label Identified"

#         return label

#     except Exception as e:
#         print("Exception:" + str(e))
#         return "No Label Identified"

# gender_index = faiss.read_index(
#     'D:\\Final_Project\\V2\\label_server\\data\\gender\\genders.index')

# with open("D:\\Final_Project\\V2\\label_server\\data\\gender\\genders_dictionary", "rb") as file:
#     gender_dictionary = pickle.load(file)


# age_index = faiss.read_index(
#     'D:\\Final_Project\\V2\\label_server\\data\\age\\age.index')
# with open("D:\\Final_Project\\V2\\label_server\\data\\age\\age_dictionary", "rb") as file:
#     age_dictionary = pickle.load(file)

# race_index = faiss.read_index(
#     'D:\\Final_Project\\V2\\label_server\\data\\race\\race.index')

# with open("D:\\Final_Project\\V2\\label_server\\data\\race\\race_dictionary", "rb") as file:
#     race_dictionary = pickle.load(file)


# vi stands for verified image.
# def build_verified_images():
#     collection = db['image_data']
#     index = faiss.IndexFlatL2(768)

#     try:
#         print("Process has started")
#         count = 0
#         # Get every image that has been verified in the db
#         for item in collection.find({"requiresVerification": "False"}):
#             if count == 0:
#                 emb = np.array(item['embedding'])
#                 embeddings = np.array(emb)
#                 count = count+1
#                 # print("Count: " + str(count))
#             else:
#                 emb = np.array(item['embedding'])
#                 embeddings = np.append(embeddings, emb, axis=0)
#                 count = count+1
#                 # print("Count: " + str(count))
#             # print(emb)
#             # vi_embeddings = np.append(vi_embeddings, emb, axis=0)
#             # vi_embeddings = np.concatenate((vi_embeddings, emb), axis=0)
#             # print("Embedding found")
#         else:
#             return vi_embeddings, vi_index

#         index.add(embeddings)

#         return embeddings, index
#     except Exception as e:
#         print(e)
#         return ("There was an error building the embeddings list.")

# def get_gender_label(embedding, nearest_neighbour_incorrect_labels):
#     try:

#         index = faiss.read_index(
#             'D:\\Final_Project\\V2\\label_server\\data\\gender\\genders.index')
#         with open("D:\\Final_Project\\V2\\label_server\\data\\gender\\genders_dictionary", "rb") as file:
#             dictionary = pickle.load(file)

#         # print("about to search index")

#         # I could use range(index.ntotal) here. But I have used range 10 for development to prevent performance issues for really big indexes.
#         D, I = index.search(embedding, 2)

#         # https://www.geeksforgeeks.org/using-else-conditional-statement-with-for-loop-in-python/
#         for count in range(int(index.ntotal)):
#             label = dictionary[I[0][count]]
#             # print("age label: " + str(label))
#             print(nearest_neighbour_incorrect_labels)

#             if label not in nearest_neighbour_incorrect_labels:
#                 break

#         else:
#             label = "No Label Identified"

#         return label

    # except Exception as e:
    #     print("Exception:" + str(e))
    #     return "No Label Identified"


# def get_age_label(embedding, nearest_neighbour_incorrect_labels):
#     try:
#         index = faiss.read_index(
#             'D:\\Final_Project\\V2\\label_server\\data\\age\\age.index')
#         with open("D:\\Final_Project\\V2\\label_server\\data\\age\\age_dictionary", "rb") as file:
#             dictionary = pickle.load(file)
#         D, I = index.search(embedding, 10)
#         # https://www.geeksforgeeks.org/using-else-conditional-statement-with-for-loop-in-python/
#         for count in range(int(index.ntotal)):
#             label = dictionary[I[0][count]]
#             if label not in nearest_neighbour_incorrect_labels:
#                 break
#         else:
#             label = "No Label Identified"
#         return label
#     except Exception as e:
#         print("Exception:" + str(e))
#         return "No Label Identified"


# def get_race_label(embedding, nearest_neighbour_incorrect_labels):
#     try:
#         index = faiss.read_index(
#             'D:\\Final_Project\\V2\\label_server\\data\\race\\race.index')
#         #print("index file read")
#         with open("D:\\Final_Project\\V2\\label_server\\data\\race\\race_dictionary", "rb") as file:
#             dictionary = pickle.load(file)

#        # print("about to search index")
#         D, I = index.search(embedding, 10)

#         # https://www.geeksforgeeks.org/using-else-conditional-statement-with-for-loop-in-python/
#         for count in range(int(index.ntotal)):
#             label = dictionary[I[0][count]]

#             if label not in nearest_neighbour_incorrect_labels:
#                 break

#         else:
#             label = "No Label Identified"

#         return label
#     except Exception as e:
#         print("Exception:" + str(e))
#         return "No Label Identified"


# def label_beard(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """

#     try:

#         #print("beard entered")
#         index = faiss.read_index(
#             'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\beard\\beard.index')
#         #print("index file read")
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\beard\\beard_dict", "rb") as file:
#             dictionary = pickle.load(file)

#        # print("about to search index")
#         D, I = index.search(embedding, 1)

#         # print(I)
#         label = dictionary[I[0][0]]
#         return label

#     except Exception as e:
#         print(e)
#         return "error"


# def label_generation(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """

#     try:
#         index = faiss.read_index(
#             "D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\generations\\generations.index")
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\generations\\generations_dict", "rb") as file:
#             dictionary = pickle.load(file)

#         D, I = index.search(embedding, 1)
#         label = dictionary[I[0][0]]
#         return label

#     except Exception as e:
#         print(e)
#         return "error"


# def label_hair_type(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """

#     try:
#         index = faiss.read_index(
#             'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\hair\\hair.index')
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\hair\\hair_dict", "rb") as file:
#             dictionary = pickle.load(file)

#         D, I = index.search(embedding, 1)
#         label = dictionary[I[0][0]]
#         return label
#     except Exception as e:
#         print(e)
#         return "error"


# def label_mouth_opened(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """
#     try:
#         index = faiss.read_index(
#             'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\mouthopened\\mouthopened.index')
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\mouthopened\\mouthopened_dict", "rb") as file:
#             dictionary = pickle.load(file)

#         D, I = index.search(embedding, 1)
#         label = dictionary[I[0][0]]
#         return label

#     except Exception as e:
#         print(e)
#         return "error"


# def label_nationality(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """

#     try:
#         index = faiss.read_index(
#             'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\nationalities\\nationalities.index')
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\nationalities\\nationalities_dict", "rb") as file:
#             dictionary = pickle.load(file)

#         D, I = index.search(embedding, 1)
#         label = dictionary[I[0][0]]
#         return label

#     except Exception as e:
#         print(e)
#         return "error"


# def label_profession(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """

#     try:
#         index = faiss.read_index(
#             'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\Professions\\professions.index')
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\Professions\\professions_dict", "rb") as file:
#             dictionary = pickle.load(file)

#         D, I = index.search(embedding, 1)
#         label = dictionary[I[0][0]]
#         return label

#     except Exception as e:
#         print(e)
#         return "error"


# def label_sex(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """

#     try:
#         index = faiss.read_index(
#             'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\sexes\\sexes.index')
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\sexes\\sexes_dict", "rb") as file:
#             dictionary = pickle.load(file)

#         D, I = index.search(embedding, 1)
#         label = dictionary[I[0][0]]
#         return label

#     except Exception as e:
#         print(e)
#         return "error"


# def label_wearing_glasses(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """
#     try:
#         index = faiss.read_index(
#             'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\wearing_glasses\\wearing_glasses.index')
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\wearing_glasses\\wearingglasses_dict", "rb") as file:
#             dictionary = pickle.load(file)

#         D, I = index.search(embedding, 1)
#         label = dictionary[I[0][0]]
#         return label

#     except Exception as e:
#         print(e)
#         return "error"


# def label_wearing_hat(embedding):
#     """
#     _summary_

#     Args:
#         embedding (_type_): _description_

#     Returns:
#         _type_: _description_
#     """
#     try:
#         index = faiss.read_index(
#             'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\wearing_hat\\wearing_hat.index')
#         with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\wearing_hat\\hat_dict", "rb") as file:
#             dictionary = pickle.load(file)

#         D, I = index.search(embedding, 1)
#         label = dictionary[I[0][0]]
#         return label

#     except Exception as e:
#         print(e)
#         return "error"
