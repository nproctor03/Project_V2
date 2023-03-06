import pickle
import faiss
import numpy as np
import pymongo


client = pymongo.MongoClient('localhost', 27017)
db = client.images

# vi stands for verified images. These are used to perform nearest neighbour search
# on images already in the db.
vi_embeddings = np.empty((0, 768), dtype=np.float32)
vi_index = faiss.IndexFlatL2(768)


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

def build_verified_images():
    collection = db['image_data']
    index = faiss.IndexFlatL2(768)

    try:
        embeddings = np.empty((0, 768), dtype=np.float32)
        print("Process has started")
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
    # print(len(vi_embeddings))
    # print(vi_index.ntotal)


def label_image(image_embedding):
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

            # closest_image_embedding_1 = closest_image_embedding_1.tolist()
            # closest_image_embedding_2 = closest_image_embedding_2.tolist()
            # closest_image_embedding_3 = closest_image_embedding_3.tolist()


# UPDATE THIS TO USE THE FIND ALL METHOD
            # nearest_neighbour_1 = db.image_data.find_one(
            #     {"embedding": closest_image_embedding_1, "requiresVerification": "False"})
            # nearest_neighbour_2 = db.image_data.find_one(
            #     {"embedding": closest_image_embedding_2, "requiresVerification": "False"})
            # nearest_neighbour_3 = db.image_data.find_one(
            #     {"embedding": closest_image_embedding_3, "requiresVerification": "False"})

            nearest_neighbour_1 = db.image_data.find(
                {"embedding": closest_image_embedding_1, "requiresVerification": "False"})

            print("query executed")

            for neighbour in nearest_neighbour_1:
                nearest_neighbour_incorrect_labels += neighbour['incorrect_labels']
                nearest_neighbour_labels += neighbour['verified_labels']
            #     nearest_neighbour_labels += neighbour['verified_labels']
            #     nearest_neighbour_incorrect_labels += neighbour['incorrect_labels']

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
            # print(nearest_neighbour_labels)

            nearest_neighbour_incorrect_labels = list(set(
                nearest_neighbour_incorrect_labels))
            # print(nearest_neighbour_incorrect_labels)

        else:
            nearest_neighbour_labels = []
            nearest_neighbour_incorrect_labels = []

        # Get the labels from the closest matching image.
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


def get_gender_label(embedding, nearest_neighbour_incorrect_labels):
    try:

        index = faiss.read_index(
            'D:\\Final_Project\\V2\\label_server\\data\\gender\\genders.index')
        with open("D:\\Final_Project\\V2\\label_server\\data\\gender\\genders_dictionary", "rb") as file:
            dictionary = pickle.load(file)

        # print("about to search index")

        # I could use range(index.ntotal) here. But I have used range 10 for development to prevent performance issues for really big indexes.
        D, I = index.search(embedding, 10)

        # https://www.geeksforgeeks.org/using-else-conditional-statement-with-for-loop-in-python/
        for count in range(10):
            label = dictionary[I[0][count]]

            if label not in nearest_neighbour_incorrect_labels:
                break

        else:
            label = "No Label Identified"

        return label

    except Exception as e:
        print(e)
        return e


def get_age_label(embedding, nearest_neighbour_incorrect_labels):
    try:
        index = faiss.read_index(
            'D:\\Final_Project\\V2\\label_server\\data\\age\\age.index')
        with open("D:\\Final_Project\\V2\\label_server\\data\\age\\age_dictionary", "rb") as file:
            dictionary = pickle.load(file)
        D, I = index.search(embedding, 10)
        # https://www.geeksforgeeks.org/using-else-conditional-statement-with-for-loop-in-python/
        for count in range(10):
            label = dictionary[I[0][count]]
            if label not in nearest_neighbour_incorrect_labels:
                break
        else:
            label = "No Label Identified"
        return label
    except Exception as e:
        # print(e)
        return e


def get_race_label(embedding, nearest_neighbour_incorrect_labels):
    try:
        index = faiss.read_index(
            'D:\\Final_Project\\V2\\label_server\\data\\race\\race.index')
        #print("index file read")
        with open("D:\\Final_Project\\V2\\label_server\\data\\race\\race_dictionary", "rb") as file:
            dictionary = pickle.load(file)

       # print("about to search index")
        D, I = index.search(embedding, 10)

        # https://www.geeksforgeeks.org/using-else-conditional-statement-with-for-loop-in-python/
        for count in range(10):
            label = dictionary[I[0][count]]

            if label not in nearest_neighbour_incorrect_labels:
                break

        else:
            label = "No Label Identified"

        return label
    except Exception as e:
        print(e)
        return e


def label_beard(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """

    try:

        #print("beard entered")
        index = faiss.read_index(
            'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\beard\\beard.index')
        #print("index file read")
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\beard\\beard_dict", "rb") as file:
            dictionary = pickle.load(file)

       # print("about to search index")
        D, I = index.search(embedding, 1)

        # print(I)
        label = dictionary[I[0][0]]
        return label

    except Exception as e:
        print(e)
        return "error"


def label_generation(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """

    try:
        index = faiss.read_index(
            "D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\generations\\generations.index")
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\generations\\generations_dict", "rb") as file:
            dictionary = pickle.load(file)

        D, I = index.search(embedding, 1)
        label = dictionary[I[0][0]]
        return label

    except Exception as e:
        print(e)
        return "error"


def label_hair_type(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """

    try:
        index = faiss.read_index(
            'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\hair\\hair.index')
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\hair\\hair_dict", "rb") as file:
            dictionary = pickle.load(file)

        D, I = index.search(embedding, 1)
        label = dictionary[I[0][0]]
        return label
    except Exception as e:
        print(e)
        return "error"


def label_mouth_opened(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        index = faiss.read_index(
            'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\mouthopened\\mouthopened.index')
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\mouthopened\\mouthopened_dict", "rb") as file:
            dictionary = pickle.load(file)

        D, I = index.search(embedding, 1)
        label = dictionary[I[0][0]]
        return label

    except Exception as e:
        print(e)
        return "error"


def label_nationality(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """

    try:
        index = faiss.read_index(
            'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\nationalities\\nationalities.index')
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\nationalities\\nationalities_dict", "rb") as file:
            dictionary = pickle.load(file)

        D, I = index.search(embedding, 1)
        label = dictionary[I[0][0]]
        return label

    except Exception as e:
        print(e)
        return "error"


def label_profession(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """

    try:
        index = faiss.read_index(
            'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\Professions\\professions.index')
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\Professions\\professions_dict", "rb") as file:
            dictionary = pickle.load(file)

        D, I = index.search(embedding, 1)
        label = dictionary[I[0][0]]
        return label

    except Exception as e:
        print(e)
        return "error"


def label_sex(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """

    try:
        index = faiss.read_index(
            'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\sexes\\sexes.index')
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\sexes\\sexes_dict", "rb") as file:
            dictionary = pickle.load(file)

        D, I = index.search(embedding, 1)
        label = dictionary[I[0][0]]
        return label

    except Exception as e:
        print(e)
        return "error"


def label_wearing_glasses(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        index = faiss.read_index(
            'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\wearing_glasses\\wearing_glasses.index')
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\wearing_glasses\\wearingglasses_dict", "rb") as file:
            dictionary = pickle.load(file)

        D, I = index.search(embedding, 1)
        label = dictionary[I[0][0]]
        return label

    except Exception as e:
        print(e)
        return "error"


def label_wearing_hat(embedding):
    """
    _summary_

    Args:
        embedding (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        index = faiss.read_index(
            'D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\wearing_hat\\wearing_hat.index')
        with open("D:\\Projects\\FlaskWebAPIs\\Label_API\\Label_API-\\data\\wearing_hat\\hat_dict", "rb") as file:
            dictionary = pickle.load(file)

        D, I = index.search(embedding, 1)
        label = dictionary[I[0][0]]
        return label

    except Exception as e:
        print(e)
        return "error"
