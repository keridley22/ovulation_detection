import pandas as pd
import numpy as np
import os
import math
import scipy
import matplotlib.pyplot as plt
import itertools
import matplotlib.dates as mdates
import boto3
import json
import boto3.session
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html#querying-and-scanning
from boto3.dynamodb.conditions import GreaterThan, Key, Attr
import dynamo_pandas
from dynamo_pandas import get_df, keys, put_df
import datetime
from datetime import timedelta
import seaborn as sns
from docx import Document
from docx.shared import Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_BREAK
#from docx.enum.table import WD_ALIGN_HORIZONTAL
from docx2pdf import convert

class getdata():
    def __init__(self, path):
        self.path = path



    def connect_dynamodb(self, region = 'eu-west-2', profile = 'default'):
        # Connect to DynamoDB
        my_session = boto3.session.Session(region_name = region, profile_name = profile)
        global dynamodb
        dynamodb = my_session.resource('dynamodb')

        return dynamodb
    
    

    def scan_table(self, dynamoTable, filterExp, expAttrNames):
    
    
        results = []
        projExp = ''
        fExp = ''
        
        # Construct ProjectionExpression string
        for key, value in expAttrNames.items() :
            if projExp == '':
                projExp = key
            else:
                projExp = projExp + ', ' + key 
            
        # Construct FilterExpression string
        for key, value in filterExp.items() :
            if fExp == '':
                fExp = 'Attr(\'{}\').eq(\'{}\')'.format(key,value)
            else:
                fExp = fExp + ' & Attr(\'{}\').eq(\'{}\')'.format(key,value) 
        
        
        response = dynamoTable.scan(
            ProjectionExpression=projExp,
            FilterExpression = eval(fExp),
            ExpressionAttributeNames = expAttrNames # Need to use ExpressionAttributeNames as some field names are reserved keywords (e.g. value)
        )
        results = response['Items']
        
        # Get all items (https://dynobase.dev/dynamodb-python-with-boto3/#scan)
        while 'LastEvaluatedKey' in response:
            response = dynamoTable.scan(ExclusiveStartKey = response['LastEvaluatedKey'],
                                        ProjectionExpression=projExp,
                                        FilterExpression = eval(fExp),
                                        ExpressionAttributeNames = expAttrNames # Need to use ExpressionAttributeNames as value is a reserved keyword
                                            )
            results.extend(response['Items'])

        return results

    def get_org_from_dynamo(self, table):

        org_df_meta=dynamo_pandas.get_df(table=table)

        inTitles = False
        while inTitles == False:
            
            org = input('Enter name of organisation: ')
                # Is prog in response?
        #         print(len(prog_df[prog_df.title == prog]))
            if len(org_df_meta[org_df_meta.name == org]) == 1:
                
                inTitles = True
                org_df = org_df_meta[org_df_meta.name == org] 

            



            else:
                inTitles=False
                print('Organisation not found. Please try again and ensure it is typed correctly')
                
                    
        print('Organisation Name: ' + str(org_df['name'].values[0]))      
            
        org_code = org_df['code'].values[0]
        org_code_GCR = org_df['groupCanRead'].values[0]
        print('Organisation code:', org_code)

        return org_code_GCR

    #get programme from org

    def get_prog_from_org(self, org_code_GCR):  
        
        prog_df_meta=dynamo_pandas.get_df(table='Study-qx7lirnxjfdzxoss6cmomxzgpe-staging')

        prog_df_org=prog_df_meta[prog_df_meta['groupCanRead']==org_code_GCR]

        if len(prog_df_org)==0:
            print('No programmes found for this organisation')
        elif len(prog_df_org)==1:
            prog=prog_df_org['title'].values[0]
            print('This organisation has one programme:', prog)
            prog_df=prog_df_org[prog_df_org['title']==prog]
        else:
            print('Please input programme from this list: ')
            print(prog_df_org['title'])
            
            inTitles = False
            while inTitles == False:
                prog = input('Enter title of programme: ')
                
                if len(prog_df_org[prog_df_org.title == prog]) == 1:
                    inTitles = True
                    prog_df = prog_df_org[prog_df_org.title == prog] 
                else:
                    print('Programme name not found. Please try again and ensure it is typed correctly')

        print('Programme title: ' + str(prog_df['title'].values[0]))      
            
        programme_id = prog_df['id'].values[0]
        print('Programme ID:', programme_id)
        return programme_id

    #Get participants
    def get_participants_from_study(self, programme_id, org_code_GCR):

        par_df_meta=dynamo_pandas.get_df(table='Athlete-qx7lirnxjfdzxoss6cmomxzgpe-staging')
        par_df_prog=par_df_meta[par_df_meta['athleteStudyId']==programme_id]
        par_id_l=[]


        if len(par_df_prog)==0:
            print('No participants found for this programme')
        elif len(par_df_prog)==1:
            par=par_df_prog['name'].values[0]
            
            par_df=par_df_prog[par_df_prog['name']==par]
            par_id = par_df['id'].values[0]
            par_id_l.append(par_id)
            print('This study has one participant:', par)
        else:
            print('This programme has', len(par_df_prog), 'participants')
            print('Please input participant name from this list | or type ALL to generate batch report: ')
            print(par_df_prog['name'])
            inTitles = False
            while inTitles == False:
                par = input('Enter name of participant, or enter ALL for batch report: ')
                
                if len(par_df_prog[par_df_prog.name == par]) == 1:
                    inTitles = True
                    par_df = par_df_prog[par_df_prog.name == par]
                    print('Participant Name: ' + str(par_df['name'].values[0]))  
                    par_id = par_df['id'].values[0]
                    par_id_l.append(par_id)
                    print('Participant ID:', par_id)
                    
                elif (par=='ALL')|(par=='all')|(par=='All'):
                    par_df=par_df_prog
                    par_id_l=list(par_df['id'])
                    inTitles = True
                    print('Generating batch report for entire programme...')
                else:
                    print('Participant not found. Please try again and ensure their name is typed correctly')

        
        return par_id_l

    def get_participants_from_org(self, org_code_GCR):

        par_df_meta=dynamo_pandas.get_df(table='Athlete-qx7lirnxjfdzxoss6cmomxzgpe-staging')
        par_id_l=[]
        

        org_code=org_code_GCR[:-4]
        orgAdmin= org_code+'Admin'

        par_df_org=par_df_meta.loc[par_df_meta['groupCanAdmin']==orgAdmin]
        
        #print(len(par_df_org_id_list), len(par_df_prog_id_list))

        if len(par_df_org)==0:
            print('No participants found for this programme')
        elif len(par_df_org)==1:
            par=par_df_org['name'].values[0]
            par_df=par_df_org[par_df_org['name']==par]
            par_id= par_df['id'].values[0]
            par_id_l.append(par_id)
            print('This organisation has one participant:', par)
        else:
            print('This organisation has', len(par_df_org), 'participants')
            print('Please input participant name from this list | or type ALL to generate batch report: ')
            print(par_df_org['name'])
            inTitles = False
            while inTitles == False:
                par = input('Enter name of participant, or enter ALL for batch report: ')
                
                if len(par_df_org[par_df_org.name == par]) == 1:
                    inTitles = True
                    par_df = par_df_org[par_df_org.name == par]
                    print('Participant Name: ' + str(par_df['name'].values[0]))  
                    
                    par_id = par_df['id'].values[0]
                    par_id_l.append(par_id)
                    print('Participant ID:', par_id)
                    
                elif (par=='ALL')|(par=='all')|(par=='All'):
                    par_df=par_df_org
                    par_id_l=list(par_df['id'])
                    inTitles = True
                    print('Generating batch report for entire organisation...')
                else:
                    print('Participant not found. Please try again and ensure their name is typed correctly')

        
        return par_id_l
    
    def get_participants_from_org_full(self, org_code_GCR):

        par_df_meta=dynamo_pandas.get_df(table='Athlete-qx7lirnxjfdzxoss6cmomxzgpe-staging')
        par_id_l=[]
        

        org_code=org_code_GCR[:-4]
        orgAdmin= org_code+'Admin'

        par_df_org=par_df_meta.loc[par_df_meta['groupCanAdmin']==orgAdmin]
        
        #print(len(par_df_org_id_list), len(par_df_prog_id_list))

        if len(par_df_org)==0:
            print('No participants found for this programme')
        elif len(par_df_org)==1:
            par=par_df_org['name'].values[0]
            par_df=par_df_org[par_df_org['name']==par]
            par_id= par_df['id'].values[0]
            par_id_l.append(par_id)
            print('This organisation has one participant:', par)
        else:
            
            inTitles = False
            while inTitles == False:
            
                    par_df=par_df_org
                    par_id_l=list(par_df['id'])
                    inTitles = True
                    print('Generating batch report for entire organisation...')
            else:
                    print('Participant not found. Please try again and ensure their name is typed correctly')

        
        return par_id_l


    def get_test_batch_codes(self, table1):
        #Fetch test batch code ids for estradiol and progesterone
        tbc_df_meta=dynamo_pandas.get_df(table=table1)
        #tbc_df_meta_p = tbc_df_meta[tbc_df_meta['participantId']==par]
        
        estradiol_tbc_l=list(tbc_df_meta.loc[(tbc_df_meta['name']=='PTP_ELISA_IBL_ESTRADIOL') | (tbc_df_meta['name']=='ELISA_IBL_ESTRADIOL') | (tbc_df_meta['name']=='ELISA_ESTRADIOL'), 'id'])
        progesterone_tbc_l=list(tbc_df_meta.loc[(tbc_df_meta['name']=='PTP_ELISA_IBL_PROGESTERONE') | (tbc_df_meta['name']=='ELISA_IBL_PROGESTERONE') | (tbc_df_meta['name']=='ELISA_PROGESTERONE'), 'id'])

        #estradiol_tbc_id = tbc_df_meta.loc[tbc_df_meta['name']=='ELISA_IBL_ESTRADIOL', 'id'].iloc[0] 
        #progesterone_tbc_id = tbc_df_meta.loc[tbc_df_meta['name']=='ELISA_IBL_PROGESTERONE', 'id'].iloc[0] 

        return estradiol_tbc_l, progesterone_tbc_l



    

    def getmostrecentkit(self, par, scan_table, table_measurement, estradiol_tbc_id):
        kit_measurements = scan_table(table_measurement,
                                        filterExp = {'measurementAthleteId' : par, 
                                        'measurementTestBatchCodeId' : estradiol_tbc_id},
                                        expAttrNames = {'#i' : 'id', '#b' : 'barcode',
                                                        '#m' : 'measurementAthleteId' , 
                                                        '#v' : 'value', 
                                                        '#k' : 'kit', 
                                                        '#c' : 'collectedAt', 
                                                        '#t':'measurementTestBatchCodeId'})


            

        measurement_df = pd.DataFrame.from_dict(kit_measurements)
        if len(measurement_df)<2:
            print('No hormone measurements found for this participant')
        else:
        
            mostrecentkit=[]


            kitlist=measurement_df.loc[measurement_df['measurementAthleteId']==par, 'kit'].unique()
            print('Finding most recent kit...')
            if len(kitlist)>0:
                kitnums = [kit[3:] for kit in kitlist]
                maxkit=max(kitnums)
                df_par_kit=measurement_df[(measurement_df['measurementAthleteId']==par) & (measurement_df['kit']=='KIT'+maxkit)]
                
                #print(len(df_par_kit))
                mostrecentkit.append(df_par_kit)
            if len(mostrecentkit)==0:
                print('No kits found for this participant ID:', par)
            else:

                df_mostrecentkit=pd.concat(mostrecentkit)

                return df_mostrecentkit

    def getallkitnums(self, par, scan_table):
        kit_measurements = scan_table

        measurement_df = pd.DataFrame.from_dict(kit_measurements)
        if len(measurement_df)==0:
            print('No hormone measurements found for this participant')
            kitlist=[]
            return kitlist
        else:
            kitlist=measurement_df.loc[measurement_df['measurementAthleteId']==par, 'kit'].unique()
            kitnums = [kit[3:] for kit in kitlist]
            print('Found kits:', kitnums)
        
            
            return kitlist

    #---------------------------------------------------------

    def get_e_df_and_p_df(self, estradiol_tbc_id_l, progesterone_tbc_id_l, scan_table):

        estradiol_measurements = scan_table

        
            
    # print(estradiol_measurements)
        estradiol_df = pd.DataFrame.from_dict(estradiol_measurements)

        estradiol_df = estradiol_df.loc[estradiol_df['measurementTestBatchCodeId'].isin(estradiol_tbc_id_l)]
        #print(estradiol_tbc_id)
        #estradiol_df = estradiol_df.loc[estradiol_df['measurementTestBatchCodeId']==estradiol_tbc_id]

        print('Number of estradiol measurements retrieved: {}'.format(len(estradiol_df)))
        
        if len(estradiol_df)>1:
            estradiol_df = estradiol_df.rename(columns = {"value" : "edata"})
            estradiol_df['collectedAt'] = pd.to_datetime(estradiol_df['collectedAt'])
            #print(estradiol_df['collectedAt'])
            estradiol_df['collectedDate'] = pd.to_datetime(estradiol_df['collectedAt']).dt.date    
            estradiol_df = estradiol_df.sort_values(by=['collectedAt'], ascending = True, ignore_index = True).drop(columns = ['collectedAt'])
            #print(estradiol_df['collectedDate'])
            #estradiol_df.loc[estradiol_df['edata'].str.contains('<'), 'edata'] = estradiol_df['edata'].str.replace('<','')
            #estradiol_df.loc[estradiol_df['edata'].str.contains('>'), 'edata'] = estradiol_df['edata'].str.replace('>','')
            estradiol_df['edata_r'] = estradiol_df['edata']
            estradiol_df.loc[estradiol_df['edata'].str.contains('<', na=False), 'edata'] = np.nan
            estradiol_df.loc[estradiol_df['edata'].str.contains('>', na=False), 'edata'] = np.nan

                
            estradiol_df['edata'] = estradiol_df['edata'].astype(float)
            #estradiol_df['edata_r'] = estradiol_df['edata_r'].astype(float)
            
            estradiol_df['linear'] = estradiol_df['edata'].interpolate(method='linear')
            e_df = estradiol_df
            e_df['collectedDate'] = pd.to_datetime(e_df['collectedDate'])
            #e_df['collectedDate'] = pd.to_datetime(e_df['collectedDate'].dt.strftime('%d/%m/%Y')) 
            #print(e_df['collectedDate'].min(), e_df['collectedDate'].max())
            e_df = e_df.set_index('collectedDate')
            e_df= e_df.loc[~e_df.index.duplicated(), :]
            e_df = e_df.resample('1D').asfreq()
            e_df['linear'] = e_df['edata'].interpolate(method='linear')
            e_df = e_df.drop(columns = ['barcode','id','kit'])
            
            #print(e_df['collectedDate'])
            
            # Calculate rolling average with a window
            window = 3
            e_df['rolling'] = e_df['linear'].rolling(window).sum()/window
            e_df['rolling'] = e_df['rolling'].shift(periods = -1)
            #e_df.loc[e_df['edata_r'].str.contains('<', na=False), 'rolling'] = np.nan
            #e_df.loc[e_df['edata_r'].str.contains('>', na=False), 'rolling'] = np.nan
            e_df_n=e_df['edata'].dropna()

            n_max=e_df_n.index.max()

            e_df.loc[e_df.index>n_max, 'rolling'] = np.nan

            e_df.head()

        else:
            e_df = pd.DataFrame()
            print('Too few estradiol measurements found')

        progesterone_measurements = scan_table

        
                
        # print(estradiol_measurements)
        progesterone_df = pd.DataFrame.from_dict(progesterone_measurements)
        progesterone_df = progesterone_df.loc[progesterone_df['measurementTestBatchCodeId'].isin(progesterone_tbc_id_l)]
        
        #progesterone_df=progesterone_df.loc[progesterone_df['measurementTestBatchCodeId']==progesterone_tbc_id]

        
        print('Number of progesterone measurements retrieved: {}'.format(len(progesterone_df)))
        if len(progesterone_df)>1:
            progesterone_df = progesterone_df.rename(columns = {"value" : "pdata"})
            progesterone_df['collectedAt'] = pd.to_datetime(progesterone_df['collectedAt'])
            progesterone_df['collectedDate'] = pd.to_datetime(progesterone_df['collectedAt']).dt.date    
            progesterone_df = progesterone_df.sort_values(by=['collectedAt'], ascending = True, ignore_index = True).drop(columns = ['collectedAt'])
            #progesterone_df.loc[progesterone_df['pdata'].str.contains('<'), 'pdata'] = progesterone_df['pdata'].str.replace('<','')
            #progesterone_df.loc[progesterone_df['pdata'].str.contains('>'), 'pdata'] = progesterone_df['pdata'].str.replace('>','')
            progesterone_df['pdata_r'] = progesterone_df['pdata']
            progesterone_df.loc[progesterone_df['pdata'].str.contains('<', na=False), 'pdata'] = np.nan
            progesterone_df.loc[progesterone_df['pdata'].str.contains('>', na = False), 'pdata'] = np.nan
            
            progesterone_df['pdata'] = progesterone_df['pdata'].astype(float)
            #progesterone_df['pdata_r'] = progesterone_df['pdata_r'].astype(float)
            
            progesterone_df['linear'] = progesterone_df['pdata'].interpolate(method='linear')
            p_df = progesterone_df
            p_df['collectedDate'] = pd.to_datetime(p_df['collectedDate'])
            p_df = p_df.set_index('collectedDate')
            p_df= p_df.loc[~p_df.index.duplicated(), :]
            p_df = p_df.resample('1D').asfreq()
            p_df['linear'] = p_df['pdata'].interpolate(method='linear')
            p_df = p_df.drop(columns = ['barcode','id','kit'])
            window = 3
            p_df['rolling'] = p_df['linear'].rolling(window).sum()/window
            p_df['rolling'] = p_df['rolling'].shift(periods = -1)
            p_df.loc[p_df['pdata_r'].str.contains('<', na=False), 'rolling'] = np.nan
            p_df.loc[p_df['pdata_r'].str.contains('>', na=False), 'rolling'] = np.nan
            p_df.head()
        else:
            p_df = pd.DataFrame()
            print('Too few progesterone measurements found')
        
        return e_df, p_df 
        #-----------------------------------------------------------------------------------------------------------------------
    def get_samples(self, scan_table):
        samples = scan_table

        print('Number of samples retrieved: {}'.format(len(samples)))
        print(samples)
        if len(samples)>0:
            samples_df = pd.DataFrame.from_dict(samples)
            samples_df['collectedAt'] = pd.to_datetime(samples_df['collectedAt'])
            samples_df['collectedDate'] = pd.to_datetime(samples_df['collectedAt']).dt.date
            samples_df['collectedTime'] = pd.to_datetime(samples_df['collectedAt']).dt.time
            samples_df = samples_df.sort_values(by=['collectedAt'], ascending = True, ignore_index = True).drop(columns = ['collectedAt'])
            return samples_df
        else:
            print('No samples found')
            return pd.DataFrame()
    
    #-----------------------------------------------------------------------------------------------------------------------
    def get_answers(self, scan_table):
        answers = scan_table
            
        answers_df = pd.DataFrame.from_dict(answers)
        if len(answers_df)==0:
            print('No answers data found')
        #get_pdf_no_symptoms(samples_df, e_df, p_df, par, export_path)
        else:
         
            answers_df['collectedDate'] = pd.to_datetime(answers_df['collectedAt']).dt.date   

        # Initialise Bleeding column
            answers_df['Bleeding'] = 'No'

            # Sort answers by collectedAt date
            answers_df = answers_df.sort_values(by=['collectedAt'], ascending = True, ignore_index = True)

            answers_df['collectedAt'] = pd.to_datetime(answers_df['collectedAt'])
            answers_df['collectedDate'] = pd.to_datetime(answers_df['collectedAt']).dt.date
            answers_df['collectedDate'] = pd.to_datetime(answers_df['collectedDate'])


            answers_df = answers_df.reset_index(drop = True)
            #----

            answers_df['Your Sleep'] = np.nan

            symptoms = ['Backache',
                        'Joint pain',
                        'Abdominal pain',
                        'Abdominal cramps',
                        'Breast tenderness',
                        'Headaches',
                        'Heavy legs',
                        'Muscle spasms',
                        'Clumsiness',
                        'Gastrointestinal upset',
                        'Food craving',
                        'Binge eating',
                        'Reduced appetite',
                        'Fatigue',
                        'Increased sex drive',
                        'Skin problems',
                        'Common cold symptoms',
                        'Low mood',
                        'Sadness',
                        'Tearful',
                        'Mood swings',
                        'Anxiety',
                        'Paranoia',
                        'Concentration loss',
                        'Confusion']

            # for symptom in symptoms:
            #     answers_df.insert(len(answers_df.columns),
            #                      symptom,
            #                      allow_duplicates=False)

            symptoms_df = pd.DataFrame(0, index=np.arange(len(answers_df)), columns=symptoms)
            # print(symptoms_df)
            answers_df = answers_df.join(symptoms_df)
            answers_df.head()

            
            # Find all days where Bleeding is reported
            for i, row in answers_df.iterrows():
                drow = json.loads(row['value'])         
                for key in drow.keys():
            #         print(drow[key])
                    if drow[key]['questionTitle'] == 'Bleeding':
                        if drow[key]['value'] == 'Yes':
                            answers_df.loc[i,'Bleeding'] = 'Yes' # Sets zero when PAR reports bleeding. This is for charting later.
                        
                    elif drow[key]['questionTitle'] == 'Your Sleep':
                        answers_df.loc[i, 'Your Sleep'] = drow[key]['value']
                        
                    elif drow[key]['questionTitle'] == 'Rate your Symptoms':
            #             print(drow[key]['value'])
                        for item in drow[key]['value']: # Each item in list is a dict with label and value
                            if 'value' in item:
                                answers_df.loc[i, item['label']] = item['value']

            bleedingdays = answers_df[answers_df['Bleeding'] == 'Yes']['collectedDate']
            bleedingdays

        return answers_df 
#-----------------------------------------------------------------------------------------------------------------------
    def aws_data_merge(self, par, kitnum, e_df, p_df,answers_df):
        e_df.rename(columns={'linear': 'E2_linear', 'rolling':'E2_rolling', 'edata':'E2'}, inplace=True)
        p_df.rename(columns={'linear': 'P4_linear', 'rolling':'P4_rolling', 'pdata':'P4'}, inplace=True)
        e_df.drop(columns=['measurementTestBatchCodeId'], inplace=True)
        p_df.drop(columns=['measurementTestBatchCodeId'], inplace=True)
        df = pd.merge(e_df, p_df, on='collectedDate', how='right')
        #get last letter of kitnum
        
        df['Cycle '] = kitnum[-1]
        df['Player'] = par

        ##create df column Day of Cycle 1-28
        

        # if answers df bleeding exists
        df['Menses'] = 0
        if 'Bleeding' in answers_df.columns:
            bleedingdays = answers_df[answers_df['Bleeding'] == 'Yes']['collectedDate']
            #match bleedingdays to df collectedDate ==1 
            df = df.reset_index()
            df['Day of Cycle'] = df.index + 1
            df.loc[df['collectedDate'].isin(bleedingdays), 'Menses'] = 1
        df = df.reset_index()
        df['Day'] = df.index + 1
        return df

    #---------------------------------------------------------------------------------------------------------------------
    def get_figure(self, answers_df, e_df, p_df):
            
        
        from datetime import timedelta
        if len(answers_df)==0:
            print('No bleeding recorded for this participant')
        else:
            bleedingdays = answers_df.loc[answers_df['Bleeding'] == 'Yes','collectedDate']
        #bleedingdays.reset_index()
        fig, (ax1) = plt.subplots(nrows=1, ncols=1, sharex = True, figsize=(10,5))
        ax2 = ax1.twinx()
        e_max=e_df.edata.max()
        
        e_df.loc[e_df['rolling']>e_max, 'rolling']==np.nan


        # Plot objects

        # e_df.reset_index().plot.area(ax = ax1, x='collectedDate', y='rolling', 
        #          color = '#FFC8D344', linewidth = 5)
        # e_df.reset_index().plot(ax = ax1, x='collectedDate', y='rolling', 
        #          color = '#DB2525')
        # p_df.reset_index().plot.area(ax = ax2, x='collectedDate', y='rolling', 
        #          color = '#BAF67F44', linewidth = 5)
        
        e_df.reset_index().plot(ax = ax1, x='collectedDate', y='rolling', 
                color = '#FFC8D3', linewidth=6, label='Oestradiol Average')
        e_df.reset_index().plot(ax = ax1, x='collectedDate', y='edata', 
                color = '#DB2525', marker = 'o', markersize = 6, linestyle = 'none', label = 'Oestradiol')
        p_df.reset_index().plot(ax = ax2, x='collectedDate', y='rolling', 
                color = 'palegreen', linewidth=6, label='Progesterone Average')
        p_df.reset_index().plot(ax = ax2, x='collectedDate', y='pdata', 
                color = 'limegreen', marker = 'o', markersize = 6, linestyle = 'none', label = 'Progesterone')

        #answers_df.reset_index().plot(ax = ax1, x='collectedDate', y = 'Bleeding',
                        #color = '#DB2525', marker = 'o', markersize = 10, linestyle = 'none')

        ylow, yhigh = ax1.get_ylim()
        xlow, xhigh = ax1.get_xlim()
        if len(answers_df)>0:
            if len(bleedingdays)>0:
                for i in range(len(bleedingdays)):


                    if i == 0:
                        
                        ax1.text(xlow+((xhigh-xlow)/20)
                        , yhigh-((yhigh-ylow)/20), 
                        'Menses', 
                                color = '#AA0E24', fontsize = 14, fontstyle = 'normal', fontweight = 'bold', horizontalalignment='left')
                            
                    ax1.axvline(bleedingdays.iloc[i], linestyle = 'None',color='crimson', marker = 'o',  markersize = 14)
            else:
                print('No bleeding recorded for this participant')

            # Set limits

        ax1.set_xlim(p_df.reset_index()['collectedDate'].min() + timedelta(days = -2), 
                    p_df.reset_index()['collectedDate'].max() + timedelta(days = 2))

        # ax1.set_ylim(0, e_df['edata'].max() + 0.5)

        # Time axis formatting
        plt.gcf().autofmt_xdate()
        #set ticks every week
        # ax1.xaxis.set_major_locator(mdates.WeekdayLocator())
        #set major ticks format
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

        ax1.set_title('Oestradiol and Progesterone: {}, {}'.format(par, kitnum), fontsize = 18)
        ax1.set_ylabel('Oestradiol, pg/mL', color = '#DB2525', fontsize = 16)
        ax2.set_ylabel('Progesterone, pg/mL', color = 'limegreen', fontsize = 16)
        ax1.set_xlabel('Date of sample collection', fontsize = 16)
        ax1.get_legend().remove()
        ax2.get_legend().remove()
        # plt.grid(True, axis = 'x' )
        ax1.grid(True, which = 'both', axis = 'x', color='#DDDDDD', linestyle='--', linewidth=1 )
        plt.savefig('{}_{}_EPchart.png'.format(par, kitnum), format='png', dpi=1200, bbox_inches='tight', facecolor='w', edgecolor='w', transparent=False)
        plt.show()

        return ax1
#----------------------------------------------------------------------------------------------------------------------
class datahandling():
    def __init__(self, dataframe, path):
        self.dataframe = dataframe
        self.path = path

    def mnc_variable_clean(self):
        data= self.dataframe 

        data['Date'] = data['Date'].str.replace('.', '/')

        data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')

        data['Menses'] = data['Menses'].replace(0, 1)

        data['Ovulation - LH peak'] = data['Ovulation - LH peak'].replace(0, 1)

        data['Ovulation - countback'] = data['Ovulation - countback'].replace(0, 1)

        return data
    
    def interpolate_data(self, data, column):
        data['{column}_interpolated'.format()] = data[column].interpolate(method='linear', limit_direction='forward', axis=0)
        window = 3
        data['{column}_rolling'.format()] = data['{column}_interpolated'.format()].rolling(window).sum()/window
        data['{column}_rolling'.format()] = data['{column}_rolling'.format()].shift(periods = -1)
        return data

    def mnc_missing_values(self, data):
        

        data = data[(data.T != 0).any()]

        data = data[(data.T != ' ').any()]

        data = data[(data.T != '0').any()]

        return data     
    
    def mnc_data_freq_split(self, data, i, j):
        
        data.loc[(data['Player'] == i) & (data['Cycle '] == j), 'Days since menses'] = data.loc[(data['Player'] == i) & (data['Cycle '] == j), 'Day'].astype(int)

        ##make column == 1 for every 3rd Day
        
        data.loc[(data['Player'] == i) & (data['Cycle '] == j) &  ((data['Day']%3==0)| ((data['Day']==1)&(data['P4']>0)) | ((data['Day']==2)&(data['P4']>0)) |  (data['Ovulation - LH peak']==1)| (data['Ovulation - countback']==1)), 'Every 3rd day'] = 1

        ##every 7th day

        data.loc[(data['Player'] == i) & (data['Cycle '] == j) & ((data['Day']%7==0)| ((data['Day']==1)&(data['P4']>0)) | ((data['Day']==2)&(data['P4']>0)) |  (data['Ovulation - LH peak']==1)| (data['Ovulation - countback']==1)) , 'Every 7th day'] = 1

        # every other day

        data.loc[(data['Player'] == i) & (data['Cycle '] == j) & ((data['Day']%2==0)| (data['Ovulation - LH peak']==1)| (data['Ovulation - countback']==1)), 'Every other day'] = 1

        ## twice a week

        data.loc[(data['Player'] == i) & (data['Cycle '] == j)& ((data['Day']%4==0) | ((data['Day']==1)&(data['P4']>0)) | ((data['Day']==2)&(data['P4']>0)) |  (data['Ovulation - LH peak']==1)| (data['Ovulation - countback']==1)), 'Twice a week'] = 1


        return data
    
    def replace_with_NaN(data, col):
        df2 = data.copy()
        columns = ['E2', 'P4']
        for column in columns:
            
            df2[column] = np.where(df2[col] != 1, np.nan, df2[column])
        return df2
    
    def closest_date_with_p4(self, df, landmark_date):

        df['Date_diff'] = abs(df['collectedDate'] - landmark_date)
        min_diff = df.loc[df['P4'].notnull(), 'Date_diff'].min()
        #print('MINDIFF HERE', min_diff)
        closest_date = df.loc[(df['Date_diff'] == min_diff) & (df['P4'].notnull()), 'collectedDate'].iloc[0]
        #print('CLOSEST DATE HERE', closest_date)
        return closest_date if not pd.isnull(closest_date) else None
    
    def hazards(self, par, kitnum, freq, org_code_gcr, progid, hazards, hazardcode, hazard):

        hazards['Participant'].append(par)
        hazards['Cycle'].append(kitnum[-1])
        hazards['Frequency'].append(freq)
        hazards['Organisation'].append(org_code_gcr)
        hazards['Programme'].append(progid)
        hazards['HazardCode'].append(hazardcode)
        hazards['Hazard'].append(hazard)

        return hazards


    

class detection():
    def __init__(self, dataframe, path):
        self.dataframe = dataframe
        self.path = path

    def baseline(self, player, cycle, column, base):
        indata = self.dataframe
        

        basel = indata[column].iloc[0:base]

        # DROP items from column basel if >90

        basel = basel[basel < 90]

        basel = basel.mean()



        df = indata
                
        df.loc[(df['Player'] == player) & (df['Cycle '] == cycle), column[:2] + '_difference'] = (df.loc[(df['Player'] == player) & (df['Cycle '] == cycle), column] / basel)*100

        return df

    def p4_ov_detect(self, data,  start_threshold):
        
        indata = data

        
        # Set the initial loop index to 4 (since we are looking 4 days prior to the first day with p4_difference > 150)
        indxlist  = indata.index.tolist()

        if len(indxlist)>4:
            threshold = indata.loc[indata['Day'] == start_threshold+1].index[0]
            #if len(countback)>0:
                #find p4 difference max after countback index
                #print(countback)
            
                #print(i)
            if len(indata.loc[threshold:])>0:
                p4diff = indata.loc[threshold:]['P4_difference'].max()
                #print(p4diff)
                if p4diff > 150:# and (indata.loc[threshold:]['P4_difference'].max()['P4']>60):
                    #if p4diff['P4']>50:
                    if indata.loc[threshold:]['P4'].max()>50:


                        i = indata.loc[indata['P4_difference'] == p4diff].index[0]
                        #print(i)
                        return i-4
                    
                    else:
                        return -1
                else:
                    return -1
            else:
                return -1
        else:
            return -1


    def p4_ov_day(self, data, start):
        
        indata = data

        indxlist  = indata.index.tolist()
        if len(indxlist)>4:
            #print(idxlist)
            i = indxlist[start+1]
            #print('startindex', i)
        else:
            i = start+1
            #print(i)

        # Use a flag variable to keep track of whether three consecutive days have been found
    
        for j in range(i, i+(len(indata))-(start+2)):
                if (indata.loc[j]['P4'] == np.nan) or (indata.loc[j]['P4'] == 0):

                    continue
            
                elif (indata.loc[j, 'P4_difference'] > 150) & (indata.loc[j, 'P4'] > 50):

                    #data.loc[j-5:j-3, 'Ovulation_region'] = 1
                    
                    return j-4
                    break
                
                else:
                    continue
                

    def e2p4_ov_day(self, indata, baird): 
        
            
            indata['E2/P4_linear'] = indata['E2/P4_linear'].replace(0, np.nan)
            indata = indata.dropna(subset=['E2/P4_linear'])
            
            indxlist  = indata.index.tolist()
            
            if len(indxlist)>4:
                
                i = indxlist[10]
                #print('startindex', i)
                count=10      
                    
            
                for j in indxlist:
                    
                    
                    newlist = indxlist[count:count+baird]
                    #print(baird, baird-1)
                    if len(newlist) < baird:
                        continue
                    elif indata.loc[newlist[baird-1]]['E2/P4']*2 <= (indata.loc[newlist[0]]['E2/P4']):
                        #data.loc[newlist[0]:newlist[baird-1], 'Bairdrange'] = 1
                        
                        return newlist[1]
                        break
                        
                    
                        
                    else:
                        count+=1
                        continue
            return None
        
    def cb_distance_metrics(self,datadict, p, c):
            mgmddict = {'Frequency':[], 'Player':[], 'Cycle':[], 'Countback Day':[], 'Kassam Day':[], 'Kassam MGMD':[]}

            for k, v in datadict.items():
                
                #print(k, v.P4.mean())
                for p in v['Player'].unique():
                    for c in v['Cycle '].unique():
                        #print(k, p, c)
                        
                        #print(k, p, c)
                        
                        if len(v.loc[(v['Player'] == p) & (v['Cycle '] == c)]) > 0:
                            mgmddict['Frequency'].append(k)
                            mgmddict['Player'].append(p)
                            mgmddict['Cycle'].append(c)

                            if len(v.loc[(v['Player'] == p) & (v['Cycle '] == c) & (v['Ovulation - countback'] == 1)]) > 0:
                                mgmddict['Countback Day'].append(v.loc[(v['Player'] == p) & (v['Cycle '] == c) & (v['Ovulation - countback'] == 1)]['Day'].values[0])
                            else:
                                mgmddict['Countback Day'].append(np.nan)
                            
                            if len(v.loc[(v['Player'] == p) & (v['Cycle '] == c) & (v['Kassam'] == 1)]) > 0:
                                mgmddict['Kassam Day'].append(v.loc[(v['Player'] == p) & (v['Cycle '] == c) & (v['Kassam'] == 1)]['Day'].values[0])
                            else:
                                mgmddict['Kassam Day'].append(np.nan)
                            
                            if (len(v.loc[(v['Player'] == p) & (v['Cycle '] == c) & (v['Kassam'] == 1)]) > 0) & (len(v.loc[(v['Player'] == p) & (v['Cycle '] == c) & (v['Ovulation - countback'] == 1)]) > 0):
                                mgmddict['Kassam MGMD'].append((v.loc[(v['Player'] == p) & (v['Cycle '] == c) & (v['Kassam'] == 1)]['Day'].values[0]) - (v.loc[(v['Player'] == p) & (v['Cycle '] == c) & (v['Ovulation - countback'] == 1)]['Day'].values[0]))
                            else:
                                mgmddict['Kassam MGMD'].append(np.nan)

                    
            mgmddata = pd.DataFrame(mgmddict)

            mgmddata.to_csv(self.path+'cycle_data_condensed.csv', index=False)

            #print(mgmddata)






            dailydict = {'Method':[], 'Frequency':[], 'Progesterone only':[]}

            for freq in mgmddata.Frequency.unique():

                ps = list[mgmddata['Player'].unique()]
                cs = list[mgmddata['Cycle'].unique()]

                #drop zeros
                ps = [x for x in ps if x != 0]
                cs = [x for x in cs if x != 0]

                #unique combinations
                psc = list(itertools.product(ps, cs))

                # if psc exists in data
                psc = [x for x in psc if x in list(zip(mgmddata['Player'], mgmddata['Cycle']))]

                total = len(psc)

                
                dailydict['Method'].append('Countback distance (Mean, SD)')
                dailydict['Frequency'].append(freq)
                dailydict['Progesterone only'].append((mgmddata.loc[(mgmddata['Frequency'] == freq)]['Kassam MGMD'].mean(), mgmddata.loc[(mgmddata['Frequency'] == freq)]['Kassam MGMD'].std()))
                

                dailydict['Method'].append('% +- 1 days')
                dailydict['Frequency'].append(freq)
                dailydict['Progesterone only'].append((len(mgmddata.loc[(mgmddata['Frequency'] == freq) & (mgmddata['Kassam MGMD'] >= -1) & (mgmddata['Kassam MGMD'] <= 1)])/total)*100)
                

                dailydict['Method'].append('% +- 2 days')
                dailydict['Frequency'].append(freq)
                dailydict['Progesterone only'].append((len(mgmddata.loc[(mgmddata['Frequency'] == freq) & (mgmddata['Kassam MGMD'] >= -2) & (mgmddata['Kassam MGMD'] <= 2)])/total)*100)
                

                dailydict['Method'].append('% +- 4 days')

                dailydict['Frequency'].append(freq)
                dailydict['Progesterone only'].append((len(mgmddata.loc[(mgmddata['Frequency'] == freq) & (mgmddata['Kassam MGMD'] >= -4) & (mgmddata['Kassam MGMD'] <= 4)])/total)*100)
                

                dailydict['Method'].append('Ovulation detected (%)')
                dailydict['Frequency'].append(freq)
                dailydict['Progesterone only'].append((len(mgmddata.loc[(mgmddata['Frequency'] == freq) & (mgmddata['Kassam MGMD'] >= -15) & (mgmddata['Kassam MGMD'] <= 15)])/total)*100)
                

            dailydf = pd.DataFrame(dailydict)

            #print(dailydf)

            dailydf.to_csv(self.path+'cb_metrics.csv')

    def plotcycle(self, data, org, p, c, f, base):

        
        #print(data['E2'])
        
            
        #value = v.loc[(v['Player']==p) & (v['Cycle ']==c)]
        #if len(value) > 5:
        #value = value.set_index('Day')
        #value = value[['P4', 'E2', 'Menses']]
        values = data.replace(0, np.nan)
        value=values
        #values = value.dropna(subset=['P4', 'E2'])

        #print(values['E2'])
        #print(value)
        #value= value.interpolate(method='linear', limit_direction='forward', axis=0)

        fig, (ax1) = plt.subplots(nrows=1, ncols=1, sharex = True, figsize=(10,5))
        ax2 = ax1.twinx()
        
        values.reset_index().plot(ax = ax1, x='Day', y='P4_rolling', color = 'palegreen', linewidth=6, label='Progesterone Average')
        values.reset_index().plot(ax = ax1, x='Day', y='P4', color = 'limegreen', marker = 'o', markersize = 6, linestyle = 'none', label = 'Progesterone')
        values.reset_index().plot(ax = ax2, x='Day', y='E2_rolling', color = '#FFC8D3', linewidth=6, label='Oestradiol Average')
        values.reset_index().plot(ax = ax2, x='Day', y='E2', color = '#DB2525', marker = 'o', markersize = 6, linestyle = 'none', label = 'Oestradiol')
        ylow, yhigh = ax1.get_ylim()
        xlow, xhigh = ax1.get_xlim()
        for i in range(len(values.loc[values['Menses']==1])):
            if i == 0:
                    
                ax1.text(xlow+((xhigh-xlow)/20)
                , yhigh-((yhigh-ylow)/20), 
                'Menses', color = '#AA0E24', fontsize = 14, fontstyle = 'normal', fontweight = 'bold', horizontalalignment='left')

                        
            ax1.axvline(value.loc[value['Menses']==1, 'Day'].iloc[i], linestyle = 'None',color='crimson', marker = 'o',  markersize = 14)

        xmin, xmax = ax1.get_xlim()
        ax1.set_xlim(xmin-2, xmax+2)
        #ax1.axvline(value.loc[value['countback estimate']==1, 'Day'].iloc[0], linestyle = '-',color='blue', marker = 'o',  markersize = 15)
        if len(value.loc[value['P4_ovulation_day']==1])>0:
            ax1.axvspan(value.loc[value['P4_ovulation_day']==1, 'Day'].iloc[0]-1, value.loc[value['P4_ovulation_day']==1, 'Day'].iloc[0]+1, color='violet', alpha=0.2)
            ax1.axvline(value.loc[value['P4_ovulation_day']==1, 'Day'].iloc[0], linestyle = '--',color='violet', marker = 'None', alpha=0.5)
        #if len(value.loc[value['Kassam+4']==1])>0:
        # ax1.axvspan(value.loc[value['Kassam+4']==1, 'Day'].iloc[0], value.loc[value['Kassam+4']==1, 'Day'].max() , alpha=0.2, color='violet')
        '''if len(value.loc[value['E2/P4_ovulation_day']==1])>0:
            ax1.axvspan(value.loc[value['E2/P4_ovulation_day']==1, 'Day'].iloc[0]-1, value.loc[value['E2/P4_ovulation_day']==1, 'Day'].iloc[0]+1, color='orange', alpha=0.2)
            ax1.axvline(value.loc[value['E2/P4_ovulation_day']==1, 'Day'].iloc[0], linestyle = '--',color='orange', marker = 'None', alpha=0.5)'''
        #if len(value.loc[value['Bairdrange']==1])>0:
            #ax1.axvspan(value.loc[value['Bairdrange']==1, 'Day'].iloc[0], value.loc[value['Bairdrange']==1, 'Day'].max() , alpha=0.2, color='orange')

        #ax1.axvline(1, linestyle = '--',color='gray', marker = 'None')
        ax1.axvspan(1, base-1, alpha=0.1, color='gray')
        #ax1.axvline(5, linestyle = '--',color='gray', marker = 'None')

        
        

                # Set limits

        #ax1.set_xlim(value.reset_index()['Day'].min() -2, value.reset_index()['Day'].max() + 2)

        # ax1.set_ylim(0, e_df['edata'].max() + 0.5)


        plt.legend('', frameon=False)
        ax1.legend('', frameon=False)

        ax2.set_ylabel('Oestradiol, pg/mL', color = '#DB2525', fontsize = 16)
        ax1.set_ylabel('Progesterone, pg/mL', color = 'limegreen', fontsize = 16)
        ax1.set_xlabel('Cycle day', fontsize = 16)
        plt.title('Player '+str(p)+' Cycle '+str(c) + ' Freq'+str(f), fontsize = 16)
        
        
        # plt.grid(True, axis = 'x' )
        #ax1.grid(True, which = 'both', axis = 'x', color='#DDDDDD', linestyle='--', linewidth=1 )
        plt.savefig(self.path + '/'+p+'/'+c+'/{}_{}_{}_{}.png'.format(org, p, c, f), format='png', dpi=1200, bbox_inches='tight', facecolor='w', transparent=False)
        plt.savefig(self.path + '/{}_{}_{}_{}.png'.format(org, p, c, f), format='png', dpi=1200, bbox_inches='tight', facecolor='w', transparent=False)
        plt.show()

    def plotcycle_no_ov(self, data, org, p, c, f):

        
        #print(data['E2'])
        
            
        #value = v.loc[(v['Player']==p) & (v['Cycle ']==c)]
        #if len(value) > 5:
        #value = value.set_index('Day')
        #value = value[['P4', 'E2', 'Menses']]
        values = data.replace(0, np.nan)
        value=values
        #values = value.dropna(subset=['P4', 'E2'])

        #print(values['E2'])
        #print(value)
        #value= value.interpolate(method='linear', limit_direction='forward', axis=0)

        fig, (ax1) = plt.subplots(nrows=1, ncols=1, sharex = True, figsize=(10,5))
        ax2 = ax1.twinx()
        
        values.reset_index().plot(ax = ax1, x='Day', y='P4_rolling', color = 'palegreen', linewidth=6, label='Progesterone Average')
        values.reset_index().plot(ax = ax1, x='Day', y='P4', color = 'limegreen', marker = 'o', markersize = 6, linestyle = 'none', label = 'Progesterone')
        values.reset_index().plot(ax = ax2, x='Day', y='E2_rolling', color = '#FFC8D3', linewidth=6, label='Oestradiol Average')
        values.reset_index().plot(ax = ax2, x='Day', y='E2', color = '#DB2525', marker = 'o', markersize = 6, linestyle = 'none', label = 'Oestradiol')
        ylow, yhigh = ax1.get_ylim()
        xlow, xhigh = ax1.get_xlim()
        for i in range(len(values.loc[values['Menses']==1])):
            if i == 0:
                    
                ax1.text(xlow+((xhigh-xlow)/20)
                , yhigh-((yhigh-ylow)/20), 
                'Menses', color = '#AA0E24', fontsize = 14, fontstyle = 'normal', fontweight = 'bold', horizontalalignment='left')

                        
            ax1.axvline(value.loc[value['Menses']==1, 'Day'].iloc[i], linestyle = 'None',color='crimson', marker = 'o',  markersize = 14)

        xmin, xmax = ax1.get_xlim()
        ax1.set_xlim(xmin-2, xmax+2)
        #ax1.axvline(value.loc[value['countback estimate']==1, 'Day'].iloc[0], linestyle = '-',color='blue', marker = 'o',  markersize = 15)
        '''if len(value.loc[value['P4_ovulation_day']==1])>0:
            ax1.axvspan(value.loc[value['P4_ovulation_day']==1, 'Day'].iloc[0]-1, value.loc[value['P4_ovulation_day']==1, 'Day'].iloc[0]+1, color='violet', alpha=0.2)
            ax1.axvline(value.loc[value['P4_ovulation_day']==1, 'Day'].iloc[0], linestyle = '--',color='violet', marker = 'None', alpha=0.5)
        #if len(value.loc[value['Kassam+4']==1])>0:
        # ax1.axvspan(value.loc[value['Kassam+4']==1, 'Day'].iloc[0], value.loc[value['Kassam+4']==1, 'Day'].max() , alpha=0.2, color='violet')
        if len(value.loc[value['E2/P4_ovulation_day']==1])>0:
            ax1.axvspan(value.loc[value['E2/P4_ovulation_day']==1, 'Day'].iloc[0]-1, value.loc[value['E2/P4_ovulation_day']==1, 'Day'].iloc[0]+1, color='orange', alpha=0.2)
            ax1.axvline(value.loc[value['E2/P4_ovulation_day']==1, 'Day'].iloc[0], linestyle = '--',color='orange', marker = 'None', alpha=0.5)
        #if len(value.loc[value['Bairdrange']==1])>0:
            #ax1.axvspan(value.loc[value['Bairdrange']==1, 'Day'].iloc[0], value.loc[value['Bairdrange']==1, 'Day'].max() , alpha=0.2, color='orange')

        #ax1.axvline(1, linestyle = '--',color='gray', marker = 'None')
        ax1.axvspan(1, 10, alpha=0.1, color='gray')'''
        #ax1.axvline(5, linestyle = '--',color='gray', marker = 'None')



        plt.legend('', frameon=False)
        ax1.legend('', frameon=False)

        ax2.set_ylabel('Oestradiol, pg/mL', color = '#DB2525', fontsize = 16)
        ax1.set_ylabel('Progesterone, pg/mL', color = 'limegreen', fontsize = 16)
        ax1.set_xlabel('Cycle day', fontsize = 16)
        plt.title('Player '+str(p)+' Cycle '+str(c)+' Freq '+str(f), fontsize = 18)
        
        
        # plt.grid(True, axis = 'x' )
        #ax1.grid(True, which = 'both', axis = 'x', color='#DDDDDD', linestyle='--', linewidth=1 )
        plt.savefig(self.path + '/'+'Without_ovulation_markers'+'/{}_{}_{}_{}.png'.format(org, p, c, f), format='png', dpi=1200, bbox_inches='tight', facecolor='w', transparent=False)
        plt.show()

        
 