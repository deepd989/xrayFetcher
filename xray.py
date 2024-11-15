import json
import requests
import re
import os
import pandas as pd
import time

cookies = {
    'key':"JSESSIONID",
    'value':"node01x4ki34dmugl31bqqn17vk7khp496.node0"
    }

errors={}

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
    response.raise_for_status()  # Raise an error for bad status codes
    
    responseData=response.json()['responseObject']
    if(not responseData):
        return []
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

        raise Exception(f"Failed to fetch image dto. Status code: {response.status_code}")
        
def download_image(imgResponse,imageName,folderDir,name):
    #replace .jpg with extension present in the path
    save_path=f'{imageName}.jpg'
    save_path=save_path.replace('/', '_')
    try:
        with open(folderDir+'/'+save_path, 'wb') as file:
            file.write(imgResponse.content)
    except Exception as e:
        message=f"An error occurred while downloading the image {str(e)}"
        storeError(name,message)
        print("An error occurred while downloading the image:", e)


def getImage(path,name):
    match=re.search(r'Customer/(.*)', path)
    if not match:
        message=f"COULDNT PARSE IMAGE PATH {path}"
        storeError(name,message)
        raise Exception("COULDNT PARSE IMAGE PATH",path)
    url='https://smr.identalcloud.com/MyDental_persistent/Customer/'+match.group(1)
    global cookies
    headers = {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        'Cookie': 'IDS_AUTH_PERSISTENT=AAA:login:Virtualteam:UcCH17VIItiqr',
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


def convertToDto(imageApiData):
    metadata={}
    metadata['path']=imageApiData.get('imagePath')
    metadata['name']=imageApiData.get('imageName')
    metadata['id']=str(imageApiData.get('id'))
    return metadata


def getPaginatedImages(memberId,skipCount,settingDto):
    url=f'https://smr.identalcloud.com/MyDental/service/imaging/getLazyLoadingImages/{memberId}/{skipCount}'
    payload=settingDto
    auth={
        cookies['key']:cookies['value']
    }
    response = requests.post(url, json=payload,cookies=auth)
    # print("POST request response:", response.json())
    response.raise_for_status()  # Raise an error for bad status codes
    
    imageDataArr=response.json()['responseObject']
    if(imageDataArr == None):
        raise Exception(f'Invalid Paginated Response Result {memberId}, {skipCount} ')
    if(len(imageDataArr)==0):
        return []
    return imageDataArr

    


def getSubsequentImages(memberId,skipCount,settingDto,name):
    errorCount=0
    finalResult=[]
    while skipCount!=-1:
        try:
            data=getPaginatedImages(memberId,skipCount,settingDto)
            if(len(data)==0):
                skipCount=-1
            else:
                finalResult.extend(data)
                skipCount+=len(data)
            
        except Exception as e:
            if(errorCount>=5):
                message=f"Error Encountered while fetching paginatedData {str(e)}"
                storeError(name,message)
                raise Exception(message)
            else:
                print("retrying for paginated data",errorCount)
            errorCount+=1
    return finalResult





def getImageDataForMember(memberId,name):
    #load initial data
    responseObj=getImageDto(memberId)['responseObject']
    settingsDto=responseObj['settingDto']
    if(not responseObj):
        storeError(name,'Invalid Image DTO')
        raise Exception('Invalid Image DTO')
    data=responseObj['userImageDtos']
    imageMetadata=[]
    for imageApiData in data:
        imageMetadata.append(imageApiData)
    imageMetadata.extend(getSubsequentImages(memberId,len(data),settingsDto,name))
    return imageMetadata
    



def getImageData(memberIds,name):
    patientData={}
    for id in memberIds:
        try:
            data=getImageDataForMember(id,name)
            imageMetadata=[]
            for imageDto in data:
                if(not isinstance(imageDto,dict)):
                    continue
                metadata=convertToDto(imageDto)
                imageMetadata.append(metadata)
            patientData[id]=imageMetadata
        except Exception as e:
            message=f"Couldnt prepare patient image dto {id}, {str(e)}",
            print(message)
            storeError(name,message)
    return patientData


def read_excel_column(file_path, sheet_name, column_name):
    try:
        # Load the specific sheet from the Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Check if the column exists in the sheet
        if column_name in df.columns:
            # Return the specific column
            return df[column_name]
        else:
            print(f"Column '{column_name}' not found in sheet '{sheet_name}'.")
            return None
    except Exception as e:
        print(f"Couldnt find excel colum {e}")
        return None


def storeError(name,message):
    global errors
    if(name in errors):
        errors[name].append(message)
    else:
        errors[name]=[message]

    





    






def getPatientXray(name):
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
        print("Search 2 failed", e)

    if(len(data1)==0 and len(data2)==0):
        #handle patient not found error
        global errors
        errors[name]=['Patient Not Found Via Search1 and Search2']
        return 
    
    memberIds=list(set(data1+data2))
    print("memberIDs ",memberIds)

    patientData=getImageData(memberIds,name)
            
    print(f"Got image DTOs for {memberIds} initiating download")
    patientIdx=0   
    for id in patientData:
        try:
            directory=f'downloads/{clinicName}/{str(rowNumber)}/'+str(id)+"_"+name.replace(" ","_")+"_"+str(patientIdx)
            os.makedirs(directory, exist_ok=True)
            patientImageMetaData=patientData[id]
            idx=0
            for metadata in patientImageMetaData:
                path=metadata['path']
                imgResponse=getImage(path,name)
                download_image(imgResponse,f"{metadata['name']}-{id}-{str(idx)}",directory,name)
                # time.sleep(0.25)
                print(f"Downloaded {idx} file from {len(patientImageMetaData)} for patient {id}")
                idx+=1
            print(f"Download Complete, downloaded {idx} files of {len(patientImageMetaData)}")
            patientIdx+=1
            
            
        except Exception as e:
            #log error
            message=f"COULDNT FETCH IMAGE DTO for {id},{str(e)}"
            storeError(name,message)
            print(f"COULDNT FETCH IMAGE DTO for {id}",e)


clinicName='Revere'
rowNumber=250
col=read_excel_column("input_sheet.xlsx",clinicName,'Patient')
patientNames=[]
for entry in col:
    data=entry.split(',')
    data=[s.strip() for s in data]
    patientNames.append(data[1]+" "+data[0])

maxPages=5
nameDict={}
while True:
    end=min(rowNumber+51,len(patientNames))
    print("fetching patient",rowNumber,end)
    idx=0
    for name in patientNames[rowNumber:end]:
        if(name in nameDict):
            idx+=1
        else:
            print("fetching",name,idx)
            getPatientXray(name) 
            idx+=1
            nameDict[name]=True
    # Construct the directory path
    directory_path = f"downloads/{clinicName}/{str(rowNumber)}"
    os.makedirs(directory_path, exist_ok=True)
    # Write JSON data to the file
    with open(f"{directory_path}/errors.json", "w") as file:
        json.dump(errors, file, indent=5)
    if(len(patientNames)<=end):
        break
    if(maxPages*50<=rowNumber):
        break
    rowNumber+=50
    







# getPatientXray("Rubila Argueta")
    



     

        
