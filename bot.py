import json
import discord
from dotenv import load_dotenv
import os
import requests
import sqlite3
from requests.structures import CaseInsensitiveDict
con = sqlite3.connect("bot.db")
cur = con.cursor()

load_dotenv() 

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('!calc'):
        operation = str(message.content.split(' ')[1])
        def calc(op):   
            if op.__contains__('+'):
                num1 = float(op.split('+')[0])
                num2 = float(op.split('+')[1])
                return num1 + num2
            elif op.__contains__('-'):
                num1 = float(op.split('-')[0])
                num2 = float(op.split('-')[1])
                return num1 - num2
            elif op.__contains__('x'):
                num1 = float(op.split('x')[0])
                num2 = float(op.split('x')[1])
                return num1 * num2
            elif op.__contains__('/'):
                num1 = float(op.split('/')[0])
                num2 = float(op.split('/')[1])
                return num1 / num2
        result = calc(operation)
        await message.channel.send(f'El resultado es: {result}')

    if message.content.startswith('!pais'):
        message_new = await message.channel.send('Cargando...')
        country = str(message.content.split(' ')[1])
        response_raw = requests.get(f'https://restcountries.com/v3.1/name/{country}')
        response = response_raw.json()
        country_name = response[0]['name']['common']
        flag = response[0]['flags']['png']
        await message_new.edit(content=f"""
        {flag}
        \nNombre: {country_name}
        """)
    
    if message.content.startswith('!help'):
        await message.channel.send('''
        **Comandos**:
        \n PARA USAR EL BOT DEL MUNDIAL TIENES QUE:
        1- **!registro** NOMBRE GMAIL CONTRASEÑA REPETIR CONTRASEÑA
        2- **!iniciar** GMAIL CONTRASEÑA
        Nota : AL PASAR 24 HORAS TIENES QUE VOLVER A INICIAR SESION
        ----------------------------------------------------------------------------
        **Comandos**
        !equipo: Busca el equipo del pais que introduzcas
        !partidos: Busca todos los partidos del pais que intruduzcas
        !grupo:Busca los equipos del grupo que introduces: A,B,C,D,E,F,G,H
        ----------------------------------------------------------------------------------
        \n!pais: busca la informacion de un pais
        \nnota: si el nombre del pais consta mas de dos palabras deben ser separadas con un guion (-)
        \n!calc: Una pequeña calculadora
        ''')

    if message.content.startswith('!registro'):
        discord_id = message.author.id
        name = message.content.split(' ')[1]
        email = message.content.split(' ')[2]
        password = message.content.split(' ')[3]
        password_match = message.content.split(' ')[4]
        data_to_json = f'{{ "name": "{name}", "email": "{email}", "password": "{password}", "passwordConfirm": "{password_match}" }}'
        json_body = json.loads(data_to_json)
        response = requests.post('http://api.cup2022.ir/api/v1/user', json=json_body)
        data_response = response.json()
        if data_response["status"] == "success":
            cur.execute("""
            INSERT INTO users (discord_id, name, email, password) VALUES (?, ?, ?, ?)
            """, [discord_id, name, email, password])
            con.commit()
            await message.channel.send('Usuario creado')
        else:
            await message.channel.send('Ha habido un error:(')

    if message.content.startswith('!iniciar'):
        email = message.content.split(' ')[1]
        password = message.content.split(' ')[2]
        data_to_json = f'{{ "email": "{email}", "password": "{password}" }}'
        json_body = json.loads(data_to_json)
        response = requests.post('http://api.cup2022.ir/api/v1/user/login', json=json_body)
        data_response = response.json()
        token = data_response["data"]["token"]
        discord_id = message.author.id
        if data_response["status"] == "success":
            cur.execute(f"""
            UPDATE users 
            SET token = ?
            WHERE discord_id = {discord_id}
            """, [token])
            con.commit()
            await message.channel.send('Iniciaste sesion')
        else:
            await message.channel.send('Ha habido un error:(')
    
    if message.content.startswith('!equipo'):
        message_new = await message.channel.send('Cargando...')
        equipo = message.content.split(' ')[1].capitalize()
        token = cur.execute(f"""
            SELECT token FROM users
            WHERE discord_id = {message.author.id}
            """)
        con.commit()
        def convertTuple(tup):
            str = ''.join(tup)
            return str
        respose_db = token.fetchone()
        tokenporfin = convertTuple(respose_db)
        headers =  CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = f"Bearer {tokenporfin}"
        response = requests.get('http://api.cup2022.ir/api/v1/team/', headers=headers)
        data_response = response.json()
        def getTeam(name):
            for team in data_response["data"]:
                if team["name_en"] == name:
                    return team

        equipito = getTeam(equipo)
        if equipito is None:
            await message_new.edit(content=f'Este equipo no existe en el mundial, ingrese otro equipo')
        else:
            fifa_code = equipito['fifa_code']
            flag = equipito['flag']
            grupos = equipito['groups']
            nombre = equipito['name_en']
            await message_new.edit(content=f'''
            \nPais: {nombre}
            \nFifa Code : {fifa_code}
            \nGrupo: {grupos}
            ''')
            await message.channel.send(f'{flag}')
            


    if message.content.startswith('!partidos'):
        equipo = message.content.split(' ')[1].capitalize()
        token = cur.execute(f"""
            SELECT token FROM users
            WHERE discord_id = {message.author.id}
            """)
        con.commit()
        def convertTuple(tup):
            str = ''.join(tup)
            return str
        respose_db = token.fetchone()
        tokenporfin = convertTuple(respose_db)
        headers =  CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = f"Bearer {tokenporfin}"
        response = requests.get('http://api.cup2022.ir/api/v1/match', headers=headers)
        data_response = response.json()
        print(data_response)
        for team in data_response["data"]:
            arr = [team["home_team_en"] == equipo]
            for t in arr:
                if t == True:
                    home = team["home_team_en"]
                    away = team["away_team_en"]
                    jornada = team['matchday']
                    await message.channel.send(f'jornada:{jornada}')
                    await message.channel.send(f'{home} vs {away}')
        for team in data_response["data"]:
            ar2 = [team["away_team_en"] == equipo]
            for te in ar2:
                if te == True:
                    home = team["home_team_en"]
                    away = team["away_team_en"]
                    jornada = team['matchday']
                    await message.channel.send(f'jornada:{jornada}')
                    await message.channel.send(f'{home} vs {away}')

    if message.content.startswith('!grupo'):
        message_new = await message.channel.send('Cargando...')
        grupo = message.content.split(' ')[1].capitalize()
        token = cur.execute(f"""
            SELECT token FROM users
            WHERE discord_id = {message.author.id}
            """)
        con.commit()
        def convertTuple(tup):
            str = ''.join(tup)
            return str
        respose_db = token.fetchone()
        tokenporfin = convertTuple(respose_db)
        headers =  CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = f"Bearer {tokenporfin}"
        response = requests.get(f'http://api.cup2022.ir/api/v1/standings/{grupo}', headers=headers)
        data_response = response.json()
        
        if data_response["status"] == "success":  
            for grupo in data_response["data"]:
                a = (grupo['teams'][0]['name_en'])
                b = (grupo['teams'][1]['name_en'])
                c = (grupo['teams'][2]['name_en'])
                d = (grupo['teams'][3]['name_en'])

                await message_new.edit(content=f'''
                Equipos:
                {a}
                {b}
                {c}
                {d}
                ''')
        else:
            await message_new.edit(content=f'Este grupo no existe, intenta con otro')
    
        

            

      

        
                                

                

 
                    
               
                

                    

        # def get(name):
        #     for team in data_response["data"]:
        #          if team["away_team_en"] == name:
        #             return team

        # partido_visitante = get(equipo)
        # grupo = partido['group']
        # jornada = partido['matchday']
        # equipo_local = partido['home_team_en']
        # equipo_visitante = partido['away_team_en']
        # jornada_visitante = partido_visitante['matchday']
        # local = partido_visitante['home_team_en']
        # visitante = partido_visitante['away_team_en']

        # await message.channel.send(f'''
        # Grupo: {grupo}
        # Local
        # jornada : {jornada}
        # {equipo_local} VS {equipo_visitante}
        # Visitante
        # jonada:{jornada_visitante}
        # {local} vs {visitante}
        # ''')
            


    

    



        

      




        
    
        

    
        



    


client.run(os.environ['TOKEN'])