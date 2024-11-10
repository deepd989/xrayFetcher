import requests
import re

cookies = {
    'key':"JSESSIONID",
    'value':"node0fnpfw1ezgpsj1oksj4pdt86rl124.node0"
    }

def search(name,url):
    payload = {
        "firstName": name,
        "offset": 28,
        "pageIndex": 1,
        "searchAllOffice": True,
        "searchInActive": True,
        "searchNewPatient": True,
        "sortedASC": True,
        "sortedKey": 1
    }

    global cookies
    auth={
        cookies['key']:cookies['value']
    }
    response = requests.post(url, json=payload,cookies=auth)
    # print("POST request response:", response.json())
    response.raise_for_status()  # Raise an error for bad status codes
    
    responseData=response.json()['responseObject']
    if(not responseData):
        raise Exception('Invalid Search Result '+name)
    patients=responseData['lstObject']
    if(len(patients)==0):
        return []
    return list(set([patient['id'] for patient in patients]))


def getImageDto(patient_id):
    url = f'https://smr.identalcloud.com/MyDental/service/imaging/getLazyLoadingImagesFirstTime/{patient_id}/0'
    global cookies

    headers = {
        'accept': 'application/json, text/html',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'connection': 'keep-alive',
        'cookie': f'{cookies['key']}={cookies['value']}',
        'host': 'smr.identalcloud.com',
        'pragma': 'no-cache',
        'referer': 'https://smr.identalcloud.com/MyDental/Dashboard',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    # Send the GET request
    response = requests.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()  # Return the response as a Python dictionary (parsed JSON)
    else:

        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
        
def download_image(imgResponse,imageName):
    #replace .jpg with extension present in the path
    save_path=f'{imageName}.jpg'
    save_path=save_path.replace('/', '_')
    print(save_path)
    try:
        with open(save_path, 'wb') as file:
            file.write(imgResponse.content)
        print(f"Image downloaded successfully and saved to {save_path}")
    except requests.exceptions.RequestException as e:
        print("An error occurred while downloading the image:", e)


def getImage(path):
    match=re.search(r'Customer/(.*)', path)
    if not match:
        raise Exception("COULDNT PARSE PATH",path)
    url='https://smr.identalcloud.com/MyDental_persistent/Customer/'+match.group(1)
    global cookies
    headers = {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        'Cookie': 'IDS_AUTH_PERSISTENT=AAA:login:Virtualteam:PvWZKFEUi2Rp3',
        "Host": "smr.identalcloud.com",
        "Pragma": "no-cache",
        "Referer": "https://smr.identalcloud.com/MyDental/Dashboard",
        "Sec-CH-UA": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"macOS"',
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    } 
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes
    return response

    

    





    






def main():
    name='Joanna'+" "+'Abou-baker'
    url1='https://smr.identalcloud.com/MyDental/service/patients/search2'
    url2='https://smr.identalcloud.com/MyDental/service/patients/search2TotalRecords'
    data1=[]
    data2=[]
    try:
        data1=search(name,url1)
    except Exception as e:
        print("An error occurred in 1", e)
        
    try:
        data2=search(name,url2)
    except Exception as e:
        print("An error occurred in 2", e)

    if(len(data1)==0 and len(data2)==0):
        #handle patient not found error
        print("PATIENT NOT FOUND",name)
        return 
    
    memberIds=list(set(data1+data2))
    print("memberIDs ",memberIds)
    patientData={}
    for id in memberIds:
        try:
            responseObj=getImageDto(id)['responseObject']
            if(not responseObj):
                raise Exception('Invalid DTO')
            data=responseObj['userImageDtos']
            imageMetadata=[]
            for imageDto in data:
                metadata={}
                metadata['path']=imageDto['imagePath']
                metadata['name']=imageDto['imageName']
                metadata['id']=str(imageDto['id'])
                imageMetadata.append(metadata)
            patientData[id]=imageMetadata
        except Exception as e:
            print("Couldnt prepare patient metadata",id)

            
    # print(patientData)        
    for id in patientData:
        try:
            print(id)
            patientImageMetaData=patientData[id]
            for metadata in patientImageMetaData:
                path=metadata['path']
                print(path)
                imgResponse=getImage(path)
                download_image(imgResponse,f"{metadata['name']}-{id}")

        except Exception as e:
            #log error
            print(f"COULDNT FETCH IMAGE DTO for {id}",e)


main()
    



     

        
