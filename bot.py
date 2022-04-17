from telegram import ChatAction,InlineQueryResultArticle,InlineQueryResultPhoto, ParseMode, InputTextMessageContent, Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler,Updater, InlineQueryHandler, CommandHandler, CallbackContext,MessageHandler,Filters
from telegram.utils.helpers import escape_markdown
from uuid import uuid4
import MoodleClient
import os
import random
import time
import requests
import config
import mediafire
import googledrive
from mega import Mega
import zipfile
import youtube_dl
import vdirect

def sendHtml(update,html):
    return update.message.reply_text(html, parse_mode=ParseMode.HTML)

def editHtml(message,html):
    return message.edit_text(html, parse_mode=ParseMode.HTML)

def get_file_size(file):
    file_size = os.stat(file)
    return file_size.st_size

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def req_file_size(req):
    try:
        return int(req.headers['content-length'])
    except:
        return 0

def get_url_file_name(url,req):
    try:
        if "Content-Disposition" in req.headers.keys():
            return str(re.findall("filename=(.+)", req.headers["Content-Disposition"])[0])
        else:
            import urllib
            urlfix = urllib.parse.unquote(url,encoding='utf-8', errors='replace')
            tokens = str(urlfix).split('/');
            return tokens[len(tokens)-1]
    except:
        import urllib
        urlfix = urllib.parse.unquote(url,encoding='utf-8', errors='replace')
        tokens = str(urlfix).split('/');
        return tokens[len(tokens)-1]
    return ''


def text_progres(index,max):
	try:
		if max<1:
			max += 1
		porcent = index / max
		porcent *= 100
		porcent = round(porcent)
		make_text = ''
		index_make = 1
		make_text += '\n['
		while(index_make<21):
			if porcent >= index_make * 5: make_text+='█'
			else: make_text+='░'
			index_make+=1
		make_text += ']\n'
		return make_text
	except Exception as ex:
			return ''


def uploadToCloud(update,message,file_name,file_size):
                #moodle_cache = config.getCache()
                #available_storage = moodle_cache['storage_size'] - moodle_cache['storage_current']
                #if file_size>available_storage:
                  #  config.stepAccount()
                  #  uploadToCloud(update,message,file_name,file_size)
                  #  return

                txtname = str(file_name)+'.txt'
                txt = open(txtname,'w')
                maxsize = 1024 * 1024 * config.MAX_ZIP_SIZE

                if file_size > maxsize:
                    mult_file =  zipfile.MultiFile(file_name+'.7z',maxsize)
                    zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
                    zip.write(file_name)
                    zip.close()
                    mult_file.close()

                    client = MoodleClient.MoodleClient(config.CREDENTIALS['username'],config.CREDENTIALS['password'])
                    loged = client.login()
                    if loged:
                        datas = []
                        for part in zipfile.files:
                            try:
                                part_size = get_file_size(part)
                                infotext = '<b>Nombre : '+file_name+'</b>\n'
                                infotext+= '<b>Parte : '+part+'</b>\n'
                                infotext+= '<b>Tamaño : '+sizeof_fmt(part_size)+'</b>\n'
                                infotext+= '<b>Estado : Subiendo a la Nube...</b>\n'
                                editHtml(message,infotext)
                                data = client.upload_file(part)
                                
                                vdirecturl = vdirect.generate(data['directurl'],client.userdata['token'],'8123')
                                txt.write(vdirecturl+'\n')

                                data['name'] = part
                                datas.append(data)
                                os.unlink(part)

                                #SetCache
                              #  moodle_cache['storage_current'] += part_size
                               # moodle_cache['file_list'].append({'fullname':part,'size':part_size,'url':data['url']})
                            except:pass
                        infotext = '<b>Informacion : </b>\n'
                        infotext+= '<b>Nombre : '+file_name+'</b>\n'
                        infotext+= '<b>Tamaño : '+sizeof_fmt(part_size)+'</b>\n\n'
                        infotext+= '<b>Partes : ('+str(len(datas))+')</b>\n'
                        for d in datas:
                            vdirecturl = vdirect.generate(d['directurl'],client.userdata['token'],'8123')
                            infotext+= '<a href="'+d['url'].replace('\\','').replace('//','').replace(':','://')+'">📥'+d['name']+'📥</a>\n'
                        editHtml(message,infotext)
                    else:
                        infotext = '<b>Error ddl :</b>\n'
                        infotext+= '<b>Verifique sus credenciales...</b>\n'
                        editHtml(message,infotext)
                        return
                else:
                    infotext = '<b>Informacion : </b>\n'
                    infotext+= '<b>Nombre : '+file_name+'</b>\n'
                    infotext+= '<b>Tamaño : '+sizeof_fmt(file_size)+'</b>\n'
                    infotext+= '<b>Estado : ⏫ Subiendo a la Nube ☁...</b>\n'
                    editHtml(message,infotext)

                    client = MoodleClient.MoodleClient(config.CREDENTIALS['username'],config.CREDENTIALS['password'])
                    loged = client.login()
                    if loged:
                        data = client.upload_file(file_name)
               
                        infotext = '<b>Informacion : </b>\n'
                        infotext+= '<b>Nombre : '+file_name+'</b>\n'
                        infotext+= '<b>Tamaño : '+sizeof_fmt(file_size)+'</b>\n'
                        vdirecturl = vdirect.generate(data['directurl'],client.userdata['token'])
                        print(client.userdata)
                        txt.write(vdirecturl)
                        infotext+= '<a href="'+data['url'].replace('\\','').replace('//','').replace(':','://')+'">📥Enlace Directo📥</a>\n'
                        editHtml(message,infotext)
                        #SetCache
                       # moodle_cache['storage_current'] += file_size
                     #   moodle_cache['file_list'].append({'fullname':file_name,'size':file_size,'url':data['url']})
                    else:
                        infotext = '<b>Error ddl :</b>\n'
                        infotext+= '<b>Verifique sus credenciales...</b>\n'
                        editHtml(message,infotext)
                        return
                txt.close()
                send = open(txtname,'r')
                update.message.reply_document(send)
                send.close()
                os.unlink(txtname)
               # config.saveCache(moodle_cache)

def ddl(update,url,session=None,filename='',message=None):
    try:
            if message == None:
                message = sendHtml(update,'<b>Extrayendo Infomacion...</b>')
            req = ''

            if session:
                req = session.get(url, stream = True,allow_redirects=True)
            else:
                req = requests.get(url, stream = True,allow_redirects=True)

            if req.status_code == 200:
                file_size = req_file_size(req)
                file_name = get_url_file_name(url,req)
                if filename!='':
                    file_name = filename

                infotext = '<b>Informacion : </b>\n'
                infotext+= '<b>Nombre : '+file_name+'</b>\n'
                infotext+= '<b>Tamaño : '+sizeof_fmt(file_size)+'</b>\n'
                infotext+= '<b>Estado : 📥Preparando Descarga</b>\n'
                editHtml(message,infotext)

                file_wr = open(file_name,'wb')
                chunk_por = 0
                chunkrandom = 100
                
                total = file_size

                time_start = time.time()
                time_total = 0
                size_per_second = 0

                for chunk in req.iter_content(chunk_size = 1024):
                    chunk_por += len(chunk)
                    size_per_second+=len(chunk);

                    tcurrent = time.time() - time_start
                    time_total += tcurrent
                    time_start = time.time()

                    file_wr.write(chunk)

                    if time_total>=1:
                        progres_text = text_progres(chunk_por,total)
                        infotext = '<b>Informacion : </b>\n'
                        infotext+= '<b>Nombre : '+file_name+'</b>\n'
                        infotext+= '<b>Estado : 📥Descargando...</b>\n'
                        infotext+= '<b>'+'Progreso:\n'+str(progres_text)+'\nDescargado: '+str(round(float(chunk_por) / 1024 / 1024, 2))+' MB\nTotal: ' +str(round(total / 1024 / 1024, 2))+ ' MB'+'</b>\n'
                        infotext+= '<b>'+'Velocidad: '+sizeof_fmt(size_per_second)+' /s</b>\n'
                        try:
                            editHtml(message,infotext)
                        except:pass
                        time_total = 0
                        size_per_second = 0

                file_wr.close()

                uploadToCloud(update,message,file_name,file_size)
               
                os.unlink(file_name)
    except Exception as ex:
                print(str(ex))
                infotext = '<b>Error ddl :</b>\n'
                infotext+= '<b>'+str(ex)+'</b>\n'
                editHtml(message,infotext)

def sendFiles(update):
    message = sendHtml(update,'<b>Extrayendo Archivos...</b>')
    client = MoodleClient.MoodleClient(config.CREDENTIALS['username'],config.CREDENTIALS['password'])
    loged = client.login()
    if loged:
        files = client.getFiles()
        infoText = '<b>Archivos: ('+str(len(files))+')</b>\n'
        i = 0
        for f in files:
            url = client.getDirectUrl(f['url'])
            fullname = get_url_file_name(url,'').split('?')[0]
            vdirecturl = vdirect.generate(url)
            infoText += '<b>'+str(i)+' - </b><a href="'+vdirecturl+'">📥 '+fullname+' ✅</a>\n'
            i+=1
        editHtml(message,infoText)
    else:
        infotext = '<b>Error :</b>\n'
        infotext+= '<b>Verifique sus credenciales...</b>\n'
        editHtml(message,infotext)

def delFile(update,index):
    message = sendHtml(update,'<b>Extrayendo Archivos...</b>')
    client = MoodleClient.MoodleClient(config.CREDENTIALS['username'],config.CREDENTIALS['password'])
    loged = client.login()
    if loged:
        files = client.getFiles()
        ff = files[index]
        fullname = get_url_file_name(ff['url'],'').split('?')[0]
        editHtml(message,'<b>Eliminando '+fullname+'...</b>')
        client.delteFile(ff['fullname'])
        editHtml(message,'<b>'+fullname+' Eliminado!</b>')
    else:
        infotext = '<b>Error :</b>\n'
        infotext+= '<b>Verifique sus credenciales...</b>\n'
        editHtml(message,infotext)

def delFiles(update):
    message = sendHtml(update,'<b>Extrayendo Archivos...</b>')
    client = MoodleClient.MoodleClient(config.CREDENTIALS['username'],config.CREDENTIALS['password'])
    loged = client.login()
    if loged:
        files = client.getFiles()
        for ff in files:
            fullname = get_url_file_name(ff['url'],'').split('?')[0]
            editHtml(message,'<b>Eliminando '+fullname+'...</b>')
            client.delteFile(ff['fullname'])
            editHtml(message,'<b>'+fullname+' Eliminado!</b>')
    else:
        infotext = '<b>Error :</b>\n'
        infotext+= '<b>Verifique sus credenciales...</b>\n'
        editHtml(message,infotext)

def megadl(update,megaurl):
    message = sendHtml(update,'<b>Extrayendo Informacion...</b>')
    try:
                
                megadl = Mega({'verbose': True})
                megadl.login()
                info = megadl.get_public_url_info(megaurl)
                file_name = info['name']
                file_size = info['size']
                size =  sizeof_fmt(file_size)

                infotext = '<b>Informacion :</b>\n'
                infotext+= '<b>Nombre : '+file_name+'</b>\n'
                infotext+= '<b>Tamaño : '+size+'</b>\n'
                infotext+= '<b>Estado : 📥Descargando...</b>\n'
                editHtml(message,infotext)

                megadl.download_url(megaurl,dest_filename=file_name)

                infotext = '<b>Informacion : </b>\n'
                infotext+= '<b>Nombre : '+file_name+'</b>\n'
                infotext+= '<b>Tamaño : '+sizeof_fmt(file_size)+'</b>\n'
                infotext+= '<b>Estado : 📥Preparando...</b>\n'
                editHtml(message,infotext)

                uploadToCloud(update,message,file_name,file_size)
                
                os.unlink(file_name)
    except Exception as ex:
            infotext = '<b>Error megadl :</b>\n'
            infotext+= '<b>'+str(ex)+'</b>\n'
            editHtml(message,infotext)


def get_youtube_info(url):
    yt_opt = {
        'no_warnings':True,
        'ignoreerrors':True,
        'restrict_filenames':True,
        'dumpsinglejson':True,
        'format':'best[protocol=https]/best[protocol=http]/bestvideo[protocol=https]/bestvideo[protocol=http]'
              }
    ydl = youtube_dl.YoutubeDL(yt_opt)
    with ydl:
        result = ydl.extract_info(
            url,
            download=False # We just want to extract the info
        )
    return result

def filter_formats(formats):
    filter = []
    for f in formats:
        #if '(DASH video)' in f['format']: continue
        #if f['ext'] == 'mp4':
            if f['filesize']:
                 filter.append(f)
    return filter


def process_msg(update,context):
    if update.message.chat.username in config.ACCES_USERS:
        msg = update.message.text
        zipfile.files.clear()
        if '/start' in msg:
            reply_text = '<b>Bienvenido a TFreeFile</b>\n\n'
            reply_text+= '<b>Comandos:</b>\n'
            reply_text+= '<b>/files - muestra la (lista) de archivos</b>\n'
            reply_text+= '<b>/del (index) - borra el archivo index de la (lista)</b>\n'
            reply_text+= '<b>/delall - borra todos los archivos (lista)</b>\n'
            reply_text+= '<b>/sc (Tamaño) - configura el tamaño de las partes (zip)</b>\n\n'
            reply_text+= '<b>Soporte (Url):</b>\n'
            reply_text+= '<b>#mega #mediafire #youtube #googlerive #directurl</b>\n'
            sendHtml(update,reply_text)
        elif '/files' in msg:
            sendFiles(update)
        elif '/sc' in msg:
            sc = str(msg).replace('/sc ','')
            config.MAX_ZIP_SIZE = int(sc)
            sendHtml(update,'<b>config.MAX_ZIP_SIZE = '+sc+'</b>')
        elif '/acc' in msg:
            username = str(msg).replace('/acc ','')
            config.ACCES_USERS.append(username)
            sendHtml(update,'<b>config.ACCES_USERS = '+str(config.ACCES_USERS)+'</b>')
        elif '/ban' in msg:
            username = str(msg).replace('/ban ','')
            config.ACCES_USERS.append(username)
            sendHtml(update,'<b>config.ACCES_USERS = '+str(config.ACCES_USERS)+'</b>')
        elif msg == '/delall':
            try:
                delFiles(update)
            except Exception as ex:
                sendHtml(update,'<b>'+str(ex)+'</b>')
        elif '/del' in msg:
            try:
                index = int(str(msg).replace('/del ',''))
                delFile(update,index)
            except Exception as ex:
                sendHtml(update,'<b>'+str(ex)+'</b>')
        elif 'mediafire' in msg:
            try:
                 url = mediafire.get(msg)
                 ddl(update,url)
            except:
                sendHtml(update,'<b>No Mediafire Folder Suport!</b>')
        elif 'mega.nz' in msg:
             megadl(update,msg)
        elif 'drive.google' in msg:
             fileid = googledrive.parse_url(msg)['file_id']
             url,session = googledrive.getDownloadUrl(fileid)
             ddl(update,url,session)
        elif 'youtube' in msg:
             message = sendHtml(update,'<b>Extrayendo Informacion...</b>')
             videoinfo = get_youtube_info(msg)
             formats = filter_formats(videoinfo['formats'])
             buttons = []
             i = 0
             for f in formats:
                 size = 0
                 try:
                    size = sizeof_fmt(f['filesize'])
                 except:pass
                 ext = ''
                 try:
                    ext = str(f['ext'])
                 except:pass
                 btntext = f['format_note']+' - '+str(size)+' - '+ext
                 buttons.append([InlineKeyboardButton(text=btntext,callback_data='ydl '+msg+' '+str(size))])
                 i+=1
             reply_text = '<a href="'+msg+'">'+videoinfo['title']+'</a>'
             message.edit_text(text=reply_text,parse_mode=ParseMode.HTML,reply_markup=InlineKeyboardMarkup(buttons))

        elif 'http' in msg or 'https' in msg:
            ddl(update,msg)

    pass


def ytdl(update,context):
    upd = update.callback_query
    msg = upd.data

    message = sendHtml(upd,'<b>Extrayendo Informacion...</b>')

    tokens = str(msg).split(' ')
    cmd = tokens[0]
    url = tokens[1]
    size = tokens[2]

    videoinfo = get_youtube_info(url)
    formats = filter_formats(videoinfo['formats'])
    format = ''
    for f in formats:
        fsize = 0
        try:
           fsize = sizeof_fmt(f['filesize'])
        except:pass
        if fsize == size:
            format = f
            break
    file_name = videoinfo['title'] + '.' + format['ext']
    file_size = format['filesize']

    file_name = str(file_name).replace('|','').replace('"','').replace('/','')

    ddl(upd,format['url'],None,file_name,message)


    pass


def main() -> None:
    try:
        updater = Updater(config.BOT_TOKEN)

        dispatcher = updater.dispatcher

        dispatcher.add_handler(CallbackQueryHandler(pattern='ydl',callback=ytdl))
        dispatcher.add_handler(MessageHandler(Filters.text,process_msg))

        updater.start_polling()
        updater.idle()
    except Exception as ex:
        print(str(ex))
        main()


if __name__ == '__main__':
    main()
