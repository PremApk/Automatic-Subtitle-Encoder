'''
*********************************************************
*         Automatic Subtitle Encoder                    *
*********************************************************
'''
#Importing necessary library
import six
import subprocess
import ffmpeg
from google.oauth2 import service_account
from google.cloud import translate_v2 as translate
import xlwt 
from xlwt import Workbook
import time
import pysrt
import xlrd
import os
from google.cloud import storage
import shlex
import ntpath
import tkinter as tk
from tkinter import Tk,PhotoImage,filedialog,Canvas,Button,OptionMenu,Label,Text,Entry,ttk
from PIL import Image,ImageTk

#Establishing connection with Google cloud service
obj="qwiklabs-gcp-02-1d7ac049ecb5-f44c5290617a.json"
buck_name="speech-to-text122"
credentials = service_account.Credentials.from_service_account_file(obj)
storage_client=storage.Client.from_service_account_json(obj)

#Defining available languages 
def source(source_input):
    source_language={
"Afrikaans(South Africa)":"af-ZA","Arabic(Bahrain)":"ar-BH","Arabic(Egypt)":"ar-EG","Arabic(Iraq)":"ar-IQ","Arabic(Israel)":"ar-IL","Arabic(Jordan)":"ar-JO","Arabic(Kuwait)":"ar-KW",
"Arabic(Lebanon)":"ar-LB","Arabic(Oman)":"ar-OM","Arabic(Qatar)":"ar-QA","Arabic(Saudi Arabia)":"ar-SA","Arabic(State of Palestine)":"ar-PS","Arabic(United Arab Emirates)":"ar-AE",
"Bengali(Bangladesh)":"bn-BD","Chinese,Cantonese(Traditional Hong Kong)":"yue-Hant-HK","Chinese,Mandarin(Traditional,Taiwan)":"zh-TW ","Czech(Czech Republic)":"cs-CZ",
"Danish(Denmark)":"da-DK","Dutch(Netherlands)":"nl-NL","English(Australia)":"en-AU","English(Ghana)":"en-GH","English(India)":"en-IN","English(Nigeria)":"en-NG",
"English(Philippines)":"en-PH","English(Singapore)":"en-SG","English(South Africa)":"en-ZA","English(Tanzania)":"en-TZ","English(United Kingdom)":"en-GB","English(United States)":"en-US",
"Filipino(Philippines)":"fil-PH","Finnish(Finland)":"fi-FI","French(Canada)":"fr-CA","French(France)":"fr-FR","German(Germany)":"de-DE","Gujarati(India)":"gu-IN","Hebrew(Israel)":"iw-IL",
"Hindi(India)":"hi-IN","Indonesian(Indonesia)":"id-ID","Italian(Italy)":"it-IT","Japanese(Japan)":"ja-JP","Kannada(India)":"kn-IN","Korean(South Korea)":"ko-KR","Malay(Malaysia)":"ms-MY",
"Malayalam(India)":"ml-IN","Marathi(India)":"mr-IN","Norwegian Bokmål(Norway)":"no-NO","Persian(Iran)":"fa-IR","Polish(Poland)":"pl-PL","Portuguese(Brazil)":"pt-BR",
"Portuguese(Portugal)":"pt-PT","Russian(Russia)":"ru-RU","Serbian(Serbia)":"sr-RS","Spanish(Spain)":"es-ES","Spanish(United States)":"es-US","Swedish(Sweden)":"sv-SE",
"Telugu(India)":"te-IN","Thai(Thailand)":"th-TH","Turkish(Turkey)":"tr-TR","Ukrainian(Ukraine)":"uk-UA","Urdu(Pakistan)":"ur-PK","Vietnamese(Vietnam)":"vi-VN","Zulu(South Africa)":"zu-ZA"
}
    return source_language[source_input]
def target(target_input):
    target_language={
"Afrikaans":"af","Albanian":"sq","Amharic":"am","Arabic":"ar","Armenian":"hy","Azerbaijani":"az","Basque":"eu","Belarusian":"be","Bengali":"bn","Bosnian":"bs","Bulgarian":"bg",
"Catalan":"ca","Cebuano":"ceb","Chinese(Simplified)":"zh-CN","Chinese(Traditional)":"zh-TW","Corsican":"co","Croatian":"hr","Czech":"cs","Danish":"da","Dutch":"nl","English":"en",
"Esperanto":"eo","Estonian":"et","Finnish":"fi","French":"fr","Frisian":"fy","Galician":"gl","Georgian":"ka","German":"de","Greek":"el","Gujarati":"gu","Haitian Creole":"ht",
"Hausa":"ha","Hawaiian":"haw","Hebrew":"he","Hindi":"hi","Hmong":"hmn","Hungarian":"hu","Icelandic":"is","Igbo":"ig","Indonesian":"id","Irish":"ga","Italian":"it","Japanese":"ja",
"Javanese":"jv","Kannada":"kn","Kazakh":"kk","Khmer":"km","Kinyarwanda":"rw","Korean":"ko","Kurdish":"ku","Kyrgyz":"ky","Lao":"lo","Latin":"la","Latvian":"lv","Lithuanian":"lt",
"Luxembourgish":"lb","Macedonian":"mk","Malagasy":"mg","Malay":"ms","Malayalam":"ml","Maltese":"mt","Maori":"mi","Marathi":"mr","Mongolian":"mn","Myanmar(Burmese)":"my","Nepali":"ne",
"Norwegian":"no","Nyanja(Chichewa)":"ny","Odia(Oriya)":"or","Pashto":"ps","Persian":"fa","Polish":"pl","Portuguese(Portugal,Brazil)":"pt","Punjabi":"pa","Romanian":"ro","Russian":"ru",
"Samoan":"sm","Scots Gaelic":"gd","Serbian":"sr","Sesotho":"st","Shona":"sn","Sindhi":"sd","Sinhala(Sinhalese)":"si","Slovak":"sk","Slovenian":"sl","Somali":"so","Spanish":"es",
"Sundanese":"su","Swahili":"sw","Swedish":"sv","Tagalog(Filipino)":"tl","Tajik":"tg","Tamil":"ta","Tatar":"tt","Telugu":"te","Thai":"th","Turkish":"tr","Turkmen":"tk","Ukrainian":"uk",
"Urdu":"ur","Uyghur":"ug","Uzbek":"uz","Vietnamese":"vi","Welsh":"cy","Xhosa":"xh","Yiddish":"yi","Yoruba":"yo","Zulu":"zu"
}
    return target_language[target_input]

#function to generate automatic subtitle based on user requirements
def subtitle_gen(gcs_uri,language,to_language,video_filename,output_filename):
    #Configuration done + Speech recognition
    from google.cloud import speech
    client = speech.SpeechClient(credentials=credentials)
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        language_code=language,
        audio_channel_count=2,
        enable_word_time_offsets=True)
    operation = client.long_running_recognize(config=config,audio=audio)
    result = operation.result()
    #From a huge data,collecting necessary data and storing in list
    json = []
    for section in result.results:
        data = {
            "transcript": section.alternatives[0].transcript,
            "words": []}
        for word in section.alternatives[0].words:
            data["words"].append({
                "word": word.word,
                "start_time": word.start_time.total_seconds(),
                "end_time": word.end_time.total_seconds(),
                "speaker_tag": word.speaker_tag
            })
        json.append(data)
    #From the list of words ,forming a sentence based on silence or different speaker tag
    sentences = []
    sentence = {}
    for result in json:
        for i, word in enumerate(result['words']):
            wordText = word['word']
            if not sentence:
                sentence = {language: [wordText],'speaker': word['speaker_tag'],'start_time': word['start_time'],'end_time': word['end_time']}
            # If we have a new speaker, save the sentence and create a new one:
            elif word['speaker_tag'] != sentence['speaker']:
                sentence[language] = ' '.join(sentence[language])
                sentences.append(sentence)
                sentence = {language: [wordText],'speaker': word['speaker_tag'],'start_time': word['start_time'],'end_time': word['end_time']}
            else:
                sentence[language].append(wordText)
                sentence['end_time'] = word['end_time']

            # If there's greater than one second gap, assume this is a new sentence
            if((i+6< len(result['words'])) and ((word['end_time'] < result['words'][i+1]['start_time']) or (sentence['start_time']+6 < sentence['end_time']))):
                sentence[language] = ' '.join(sentence[language])
                sentences.append(sentence)
                sentence = {}
        if sentence:
            sentence[language] = ' '.join(sentence[language])
            sentences.append(sentence)
            sentence = {}
    #Converting sentence into the target language and storing in Excel sheet with the timestamp      
    wb = Workbook()
    row,column,index=0,0,0
    sheet1 = wb.add_sheet('DATA')
    for var in sentences:
        input1=var[language]
        start_time=var['start_time']
        end_time=var['end_time']
        translate_client = translate.Client(credentials=credentials)
        if isinstance(input1,six.binary_type):
            input1=input1.decode("utf-8")
        result = translate_client.translate(input1, target_language=to_language)
        sheet1.write(row, column, index)
        index+=1
        column+=1
        sheet1.write(row, column, time.strftime('%H:%M:%S',time.gmtime(start_time)))
        column+=1
        sheet1.write(row, column, time.strftime('%H:%M:%S',time.gmtime(end_time)))
        column+=1
        sheet1.write(row, column, result['translatedText'])
        row+=1
        column=0
    wb.save('DATA.xls')
    #Creating a custom srt file and merging with the video file
    wb=xlrd.open_workbook("DATA.xls")
    sheet=wb.sheet_by_index(0)
    row,column=0,0
    total=sheet.nrows
    with open("subtitle.srt","w",encoding='UTF-8') as f:
       while(total):
           total-=1
           f.write(str(int(sheet.cell_value(row,column))+1))
           column+=1
           f.write("\n")
           f.write(str(sheet.cell_value(row,column))+",000")
           column+=1
           f.write(" --> ")
           f.write(str(sheet.cell_value(row,column))+",000")
           column+=1
           f.write("\n")
           f.write(sheet.cell_value(row,column))
           f.write("\n")
           f.write("\n")
           row+=1
           column=0
    command="ffmpeg -i "+video_filename+" -i subtitle.srt -c:s mov_text -c:v copy -c:a copy "+output_filename
    args=shlex.split(command)
    subprocess.Popen(args)
    root.destroy()
    
#main function
def call_main(video_filename):
    global length
    length=len(video_filename)
    command="ffmpeg -i "+video_filename.replace(" ","")+" "+video_filename[:length-4].replace(" ","")+".flac"
    args=shlex.split(command)
    subprocess.call(args)
    
#Methods for GUI Buttons
def pc_click():
    filename=filedialog.askopenfilename()
    path_text_obj.insert(0,filename)
    global video_filename
    video_filename=ntpath.basename(filename)
    call_main(video_filename)

def u_click():
    try:
        from pytube import YouTube
        from pytube import Playlist
    except Exception as e:
        print("Error")
    url=path_text_obj.get()
    ytd=YouTube(url)
    ytd=YouTube(url).streams.first().download()
    os.rename(ytd,ytd.replace(" ",""))
    global video_filename
    video_filename=ntpath.basename(ytd)
    call_main(video_filename)
    
def translator():
    input1=from_choice.get()
    input2=to_choice.get()
    source_lang=source(input1)
    target_lang=target(input2)
    print(source_lang)
    print(target_lang)
    output_filename=video_filename[:length-4].replace(" ","")+"(with-"+input2+"-subtitle).mp4"
    audio_filename=video_filename[:length-4].replace(" ","")+".flac"
    bucket=storage_client.get_bucket(buck_name)
    blob=bucket.blob(audio_filename)
    blob.upload_from_filename(audio_filename)
    subtitle_gen("gs://"+buck_name+"/"+audio_filename,source_lang,target_lang,video_filename.replace(" ",""),output_filename)

#Initializing Tkinter Window
root = Tk()
root.title("Automatic Subtitle Encoder")
encoder_icon = PhotoImage(file = "languages.png")
root.iconphoto(True, encoder_icon)
root.resizable(0,0)
bg_image = ImageTk.PhotoImage(Image.open("maxresdefaultfinal.jpg"))

#Creating Canvas Object
canvas = Canvas(root, width=bg_image.width(), height=bg_image.height())
canvas.create_image(0,0,anchor='nw',image=bg_image)
canvas.pack()

#Configuring Style for GUI Components
fontstyle = ("Arial Rounded MT Bold",10,"bold")
style = ttk.Style()
style.theme_create('combostyle', parent='alt', settings={'TCombobox':
                                                         {'configure':
                                                          {'fieldbackground': '#d3e0ea',
                                                            'background': '#276678',
                                                           'highlightbackground' : '#276678',
                                                           }}})
style.theme_use('combostyle')


#Text Label for required Fields
canvas.create_text(400,100, text="AUTOMATIC SUBTITLE", font=("Typo Draft Demo", 35),fill="#9fd8df")
canvas.create_text(410,150, text="ENCODER", font=("Typo Draft Demo", 35),fill = "#9fd8df")
canvas.create_text(160,300, text="Path for SRT File : ", font=("Arial Rounded MT Bold", 18),fill = "#a4ebf3")
canvas.create_text(160,550, text="Target Language : ", font=("Arial Rounded MT Bold", 18),fill = "#a4ebf3")
canvas.create_text(160,450, text="Source Language : ", font=("Arial Rounded MT Bold", 18),fill = "#a4ebf3")

#Button for PC Dialog
dialog_button_obj_pc = Button(canvas, text="PC", command=pc_click, width=12, bg="#9fd8df", font=fontstyle)
dialog_pc = canvas.create_window(350,350,window=dialog_button_obj_pc)

#Button for Youtube Reference
dialog_button_obj_youtube = Button(canvas, text="YOUTUBE", command=u_click, width=12, bg="#9fd8df", font=fontstyle)
dialog_youtube = canvas.create_window(500,350,window=dialog_button_obj_youtube)

#Creating Path text box for directory
path_text_obj = Entry(root, highlightthickness=4,width=30,highlightbackground="#276678",bg="#d3e0ea", font=fontstyle)
canvas.create_window(420,300,window=path_text_obj)

#Button for Translation
convert_button = Button(canvas, text="Translate", command=translator, width=15, bg="#9fd8df", font=fontstyle)
convert_button = canvas.create_window(380,630,window=convert_button)

#ComboBoxes for Language Selection
from_choice = ttk.Combobox(canvas,width = 25, font=fontstyle)
from_choice['values'] = ("Afrikaans(South Africa)","Arabic(Bahrain)","Arabic(Egypt)","Arabic(Iraq)","Arabic(Israel)","Arabic(Jordan)","Arabic(Kuwait)","Arabic(Lebanon)","Arabic(Oman)",
"Arabic(Qatar)","Arabic(Saudi Arabia)","Arabic(State of Palestine)","Arabic(United Arab Emirates)","Bengali(Bangladesh)","Chinese,Cantonese(Traditional Hong Kong)",
"Chinese,Mandarin(Traditional,Taiwan)","Czech(Czech Republic)","Danish(Denmark)","Dutch(Netherlands)","English(Australia)","English(Ghana)","English(India)","English(Nigeria)",
"English(Philippines)","English(Singapore)","English(South Africa)","English(Tanzania)","English(United Kingdom)","English(United States)","Filipino(Philippines)","Finnish(Finland)",
"French(Canada)","French(France)","German(Germany)","Gujarati(India)","Hebrew(Israel)","Hindi(India)","Indonesian(Indonesia)","Italian(Italy)","Japanese(Japan)","Kannada(India)",
"Korean(South Korea)","Malay(Malaysia)","Malayalam(India)","Marathi(India)","Norwegian Bokmål(Norway)","Persian(Iran)","Polish(Poland)","Portuguese(Brazil)","Portuguese(Portugal)",
"Russian(Russia)","Serbian(Serbia)","Spanish(Spain)","Spanish(United States)","Swedish(Sweden)","Telugu(India)","Thai(Thailand)","Turkish(Turkey)","Ukrainian(Ukraine)","Urdu(Pakistan)"
,"Vietnamese(Vietnam)","Zulu(South Africa)")
from_choice['state'] = 'readonly'
canvas.create_window(400,450,window=from_choice,height=20)

to_choice = ttk.Combobox(canvas,width = 25, font=fontstyle)
to_choice['values'] = ("Afrikaans","Albanian","Amharic","Arabic","Armenian","Azerbaijani","Basque","Belarusian","Bengali","Bosnian","Bulgarian","Catalan","Cebuano","Chinese(Simplified)",
"Chinese(Traditional)","Corsican","Croatian","Czech","Danish","Dutch","English","Esperanto","Estonian","Finnish","French","Frisian","Galician","Georgian","German","Greek","Gujarati",
"Haitian Creole","Hausa","Hawaiian","Hebrew","Hindi","Hmong","Hungarian","Icelandic","Igbo","Indonesian","Irish","Italian","Japanese","Javanese","Kannada","Kazakh","Khmer","Kinyarwanda",
"Korean","Kurdish","Kyrgyz","Lao","Latin","Latvian","Lithuanian","Luxembourgish","Macedonian","Malagasy","Malay","Malayalam","Maltese","Maori","Marathi","Mongolian","Myanmar(Burmese)",
"Nepali","Norwegian","Nyanja(Chichewa)","Odia(Oriya)","Pashto","Persian","Polish","Portuguese(Portugal,Brazil)","Punjabi","Romanian","Russian","Samoan","Scots Gaelic","Serbian",
"Sesotho","Shona","Sindhi","Sinhala(Sinhalese)","Slovak","Slovenian","Somali","Spanish","Sundanese","Swahili","Swedish","Tagalog(Filipino)","Tajik","Tamil","Tatar","Telugu","Thai",
"Turkish","Turkmen","Ukrainian","Urdu","Uyghur","Uzbek","Vietnamese","Welsh","Xhosa","Yiddish","Yoruba","Zulu")
to_choice['state'] = 'readonly'
canvas.create_window(400,550,window=to_choice)

#Updating Canvas
canvas.update()
root.mainloop()
