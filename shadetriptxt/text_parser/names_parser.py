import re
from ..utils import string_ops

def symbol_pattern(input_string):
    """
    Normalizes symbols in the input string.
    """
    return string_ops.normalize_symbols(input_string)


def space_pattern(input_string):
    """
    Normalizes spaces in the input string.
    """
    return string_ops.normalize_spaces(input_string)


def erase_lrspaces(input_string):
    """
    Removes leading and trailing spaces from the input string.

    Args:
        input_string (str): The string to strip.

    Returns:
        str: The stripped string.
    """
    if input_string is None:
        return None
    return input_string.strip()


def left_replace(input_string, old, new):
    """
    Replaces occurrences of old with new from the left.

    Args:
        input_string (str): The string to modify.
        old (str): The substring to replace.
        new (str): The replacement substring.

    Returns:
        str: The modified string.
    """
    if input_string is None:
        return None
    return input_string.replace(old, new, 1)  # Replace only the first occurrence


def get_companytype(input_string):
    """
    Extracts the company type from the input string.
    """
    if not input_string:
        return None
    s = string_ops.erase_allspaces(input_string).upper()
    common_forms = ['SLU', 'SAU', 'SL', 'SA', 'SRL', 'SLL', 'SC', 'CB', 'SAC', 'SCA']
    for form in common_forms:
        if s.endswith(form):
            return form
    return None


def arrange_fullname(input_name):
    """
    Rearranges a full name from "Last, First" format to "First Last".
    """
    if not isinstance(input_name, str):
        return None
    return string_ops.reorder_comma_fullname(input_name)
    


def format_name(input_string, add_charset, format_type, upper):
    if input_string is None:
        return None

    oparse = input_string

    replace_map = {
        "´":"'", "`":"'",
        "{": "(", "}": ")", "[": "(", "]": ")", "*": " ", '"': " ", "_": " ", "·": " ",
        ",": " ", ";": " ", "|": " ", "\\": " ", "¬": " ", "‰": " ", "½": " ", "ƒ": " ",
        "Ž": " ", "œ": " ", "‹": " ", "Š": " ", "˜": " ", "‡": " ", "†": " ", "¥": " ",
        "ð": " ", "§": " ", ".": " "
    }
    for char, replacement in replace_map.items():
        oparse = oparse.replace(char, replacement)

    # Eliminar caracteres no deseados y respetar add_charset
    oparse = string_ops.erase_specialchar(oparse, add_charset)

    # Corregir caracteres en español y reemplazar símbolos
    oparse = string_ops.fix_spanish(oparse, add_charset)
    
    # Aplicar patrones específicos
    oparse = symbol_pattern(oparse)
    if oparse:
        # Acomodar 'º' y 'ª'
        oparse = oparse.replace("º", "º ").replace("ª", "ª ")
        oparse = oparse.replace(" º", "º").replace(" ª", "ª")

        # Normalizar según el tipo
        if format_type == "PERSONA":
            oparse = string_ops.string_aZ(oparse, "ºª" + add_charset, True)
        else:
            oparse = string_ops.string_aZ09(oparse, "ºª" + add_charset, True)

        # Eliminar espacios redundantes
        oparse = space_pattern(oparse)
        if oparse:
            oparse = oparse.replace(" + ", "+")

    return oparse.upper() if upper and oparse else oparse


def parse_company(input_string,legal_forms):
    if input_string is None : return input_string
    else:
        islf = -1
        comtype = None
        comname = None

        oparse = input_string.replace('(EXTINGUIDA)','')
        oparse = oparse.replace('- EXTINGUIDA','')
        oparse = oparse.replace('-EXTINGUIDA','')
        oparse = oparse.replace('(EN LIQUIDACION)','')
        oparse = oparse.replace(' EN LIQUIDACION','')

        charset =  "ºª@#$%&=+-_/\\|.:[]()¿?¡!'"
        oparse = format_name(oparse,charset,'COMPANY',True)
        if oparse:
            #check if there is a legal form
            islf = oparse.find ('.')
            if islf != -1: islf = True
            else: islf = oparse.find (' ')
            if islf != -1: islf = True
            else: islf = oparse.find ('(')
            if islf != -1: islf = True

            oparse = oparse.upper() + ' ' 

            oparse = oparse.replace('SOCIEDAD LIMITADA','SL')
            oparse = oparse.replace('SOCIEDAD ANONIMA','SA')
            oparse = oparse.replace('COM PROP','COMUNIDAD DE PROPIETARIOS')
            oparse = oparse.replace('CDAD PROP','COMUNIDAD DE PROPIETARIOS')         
            oparse = oparse.replace(' ASOC ',' ASOCIACION ')
            oparse = oparse.replace(' ASOC.',' ASOCIACION ')
            if oparse.startswith('ASOC '): oparse = oparse.replace('ASOC ',' ASOCIACION ')
            if oparse.startswith('ASOC.'): oparse = oparse.replace('ASOC.',' ASOCIACION ')
            oparse = oparse.replace('SOCIEDAD DE RESPONSABILIDAD LIMITADA','SRL')                     
            oparse = oparse.replace('SOCIEDAD COOPERATIVA','SCOOP')
            oparse = oparse.replace('SOCIEDAD COOP','SCOOP')
            oparse = oparse.replace('S COOP','SCOOP')
            oparse = oparse.replace('SOCIEDAD ANONIMA LABORAL','SAL')
            oparse = oparse.replace('SOCIEDAD DE RESPONSABILIDAD LIMITADA LABORAL','SRLL')
            oparse = oparse.replace('SL LABORAL',' SLL ')
            oparse = oparse.replace('SOCIEDAD LIMITADA LABORAL','SLL')  
            oparse = oparse.replace('SA DEPORTIVA','SAD')
            oparse = oparse.replace('SL PROFESIONAL','SLP')

            oparse = oparse.replace(' SCOOPL',' SCOOP')
            oparse = oparse.replace(' SCL',' SC')

            if islf != -1:
                findtype = string_ops.erase_allspaces(oparse)
                findtype = findtype.replace('.','')
                findtype = findtype.replace('(','')
                findtype = findtype.replace(')','')

                for form in legal_forms:
                    if findtype[ - len(form):] == form:                                
                        comtype = form
                        pattern = findtype.replace(comtype,'')
                        if pattern:
                            i = 0
                            comname = ''
                            for vchar in oparse:
                                comname = comname + vchar
                                if vchar == pattern[i]:
                                    i += 1
                                if i == len(pattern):
                                    break
                        break                       

        oparse = erase_lrspaces(oparse)

        if not comtype and oparse:
            if 'COMUNIDAD DE PROPIETARIOS' in oparse: comtype = 'COMUNIDAD DE PROPIETARIOS'
            if 'COMUNIDAD DE BIENES' in oparse: comtype = 'COMUNIDAD DE BIENES'
            if 'ORGANO DE LA ADMINISTRACION' in oparse: comtype = 'ORGANO DE LA ADMINISTRACION'
            if 'ENTIDAD NO LUCRATIVA' in oparse: comtype = 'ENTIDAD NO LUCRATIVA'
            if 'CORPORACION LOCAL' in oparse: comtype = 'CORPORACION LOCAL'
            if 'SUCURSAL EN ESPAÑA' in oparse: comtype = 'SUCURSAL EN ESPAÑA'
            if 'PARTIDO POLITICO' in oparse: comtype = 'PARTIDO POLITICO'
            if 'ORGANISMO AUTONOMO' in oparse: comtype = 'ORGANISMO AUTONOMO'
            if 'ENTIDAD NO RESIDENTE' in oparse: comtype = 'ENTIDAD NO RESIDENTE'
            if 'ASOCIACION' in oparse: comtype = 'ASOCIACION'
            if 'ASSOCIACIO' in oparse: comtype = 'ASOCIACION'        
            if 'FUNDACION' in oparse: comtype = 'FUNDACION'

        if comtype and comname:
            return (comname,comtype)
        elif comtype:
            return (oparse,comtype)
        elif oparse: return (oparse,None)
        else: return None


def format_companyname(company_name, company_type, format):
    if company_name is None : return None
    else:
        comname = company_name
        if company_type:
            if not company_type in ['ORGANO DE LA ADMINISTRACION','ENTIDAD NO LUCRATIVA','CORPORACION LOCAL','SUCURSAL EN ESPAÑA', \
                'PARTIDO POLITICO','ORGANISMO AUTONOMO','ENTIDAD NO RESIDENTE','ASOCIACION','FUNDACION', \
                'CAJA','MUTUA','FONDO','N/A']:

                if format == 'brackets':
                    comtype = '(' + company_type + ')'
                elif format == 'dots' or format == 'comma&dots':
                    if len(company_type) >= 4 or company_type in ['LTD','INC','CO']:
                        comtype = company_type + '.'
                    else:
                        strtype = company_type
                        comtype = ''
                        for c in strtype:
                            comtype = comtype + c + '.'

                comtype = ' ' + comtype
                if format == 'comma&dots':
                    comtype = ',' + comtype
            else:
                if company_type == 'N/A': comtype = ''
                else:
                    comname = get_companyname(company_name,company_type)
                    comtype = ', ' + company_type   
        else:
            comtype = ''
    
    return comname + comtype


def get_companyname(company_name,company_type):
    #comname = #'CAMINO E HIJOS CB',comtype = 'CB'
    if company_name is None : return None
    else: 
        if company_type:
            if company_name[-len(company_type)-1:] == ' ' + company_type:
                oparse = left_replace(company_name, ' '+ company_type, ' ')
            else:
                oparse = company_name
        else:
            oparse = company_name

        oparse = space_pattern(oparse)
        oparse = symbol_pattern(oparse)           
        oparse = string_ops.flat_vowels(oparse)


        return oparse


def isformat_company(input_string):
    if input_string is None : return input_string
    else:
        list_companytypes = ['SCCIL','SCCL','CORP','LTD','INC','LLC','SAL','SAU','SLU','SRL','SAC' \
            ,'SCA','SLL','CO','LC','LP','AG','NV','SA','SL','SC','RL','CB','FC','S']
        
        return get_companytype(input_string.upper()) in list_companytypes



#if __name__ == "__main__":
    #instance for data_reference

    #str_parse =" Anacleto y Amigos.s L "
    #str_parse = " Pepito Grillo sa "
    #str_parse = "nada de nadasa."
    #str_parse = "vaya tela s.au"
    #str_parse = "paque,s.aU"
    #str_parse = "SERVICIOS FROS. CARREFOUR, E.F.C. S.A."
    #str_parse = "A.D.F.F., S.L."
    #str_parse = "ACADEMIA DENTAL DE MALLORCASL"
    #str_parse = "AGENCIA ARAGONESA DE NOTICIAS, S"
    #str_parse = "AGENCIA ARAGONESA DE NOTICIAS,S"
    #str_parse = "AGENCIA MODELOS DM & B SL"

    #str_parse = "DA NICOLA"

    #str_parse = "ATRES ADVERTISING , S.L.U. -B-"
    #str_parse = "ATRES ADVERTISING , S.L.U. Y BECARIOS -B-"
    #str_parse = "CAJA RURAL DE ALBACETE, CIUDAD REAL Y CUENCA, S.C.C. (GLOBALCAJA" 
    #str_parse = "ALIWOOD MEDITERRÁNEO PRODUCCIONES, S.L. (AEC)"
    #str_parse = "ALJUGOSA  S. A( GRUPO BALLESTEROS)" 
    
    #str_parse = "AGENCIA MODELOS DM & B SL"
    #str_parse = 'ASISTENCIA CLINICA UNIVERSITARIA DE NAVARRA SA DE SEGUROS Y REASEGUROS'

    #str_parse = "SERVIMIL S.A. ."
    #str_parse = "NEUMÁTICOS JOSE A. PÉREZ PARDO, S."
    #str_parse = "MORENO HIGUERAS S.L"
    #str_parse = "HERBER GESTIÓN TÉCNICA INMOB. CB"    
    #str_parse = "INNOVACION ESTÉTICA,S.L" 
    #str_parse = "ALZEIMER FUNDACION"
    #str_parse = "FUNDACION ALZEIMER"
    #str_parse = "CENTRO BAHIA OCULAR S.L."
    #str_parse = "Zoom S.c.p."
    #str_parse = 'AYUNTAMIENTO RICON DE SOTO'
    #str_parse = '36 AGENDAS AYTO'
    #str_parse = parse_company(str_parse,list_legaforms)
    
    # charset =  "ºª@#$%&=+-_/\\|.:[]()¿?¡!'"
    # str_parse = format_name(str_parse,charset,True)

    #str_parse = format_companyname(str_parse[0],str_parse[1],'comma&dots')
        

    #tup_com = ('COMPAÑIA E HIJOS CB', 'CB')
    #tup_com = ('CAJA DE AHORROS DE MADRID', 'CAJA')
    #tup_com = ('FUNDACION ONCE FUNDACION', 'FUNDACION')
    #str_parse = get_companyname(tup_com)
     


    #str_parse =  "*ºª@#$%&=+-_/\\|·.:,;[](){}¿?¡!><'\"´`’¬‰½ƒŽœ‘‹Š˜‡†¥ð§" +'\xa0'
    #charset =  "@&+:/"
    #str_parse = '1ª ¬DIVISI@N '

    #charset =  "ºª@#$%&=+-_/\\|.:[]()¿?¡!'"
    #str_parse = 'ADMINISTRATION DE L\'ETAT DE LA GUINÉE EQUATORIALE'
    #str_parse = string_aZ(str_parse,charset, False)

    #str_parse = raw_string_aZ09(str_parse,charset, False)
    
    #charset =  "*ºª@#$%&=+-_/\\|·.:,;[](){}¿?¡!><'\""
    #str_parse = '1ª ¬divisi@n [QUE_NO segunda)œ'    
    #str_parse = format_name(str_parse,charset,True,True)

    #str_parse='91.303.20.60-91 303 20 60'
    #str_parse='91-303-20-60 91 303 20 60/600606060 91.303.20.60-23023'
    #str_parse='91-303-20-60 /91 303 20 60/600606060 91.303.20.60-23023'
    #str_parse = get_phones(str_parse,'/-')

    #charset =  "ºª@#$%&=+-_/\\|.:[]()¿?¡!'"
    #str_parse = format_name('TRILLONARIO.COM',charset,True)


    # result = ('JAVIER MARTINEZ POMBO', 'jms25057')
    result = ('ESTELA MARIA COLLADO MARTINEZ', 'ecm25057')
    
    print(result)   

    str_parse = create_login_string("javier de la rodriguez garcia",'53060')

    str_parse = string_findings('esto es una prueba para encontrar a27 cadenas 2j33 con nºs y letras','cadenas_con_numeros_y_letras')    

    print(str_parse)   


    #print(OLD_get_NIF_ok('P0619900B'))

    #nif('AT','U35658506')
    #nif('ES','G28010619')
    #nif('IE', '6390845P')
    #nif('GB', '853750806')

    #str_parse = 'P0619900B'
    #str_parse = 'B30878331'
    #str_parse = '11846245A' #nif
    #str_parse = '71364033H' #nif erroneo 
    #str_parse = 'G31556699' #cif    
    #str_parse = 'P0605100G'    
    #str_parse = 'B84761857'
    #str_parse = 'B1404500I' #cif erroneo
    #'IE', '6390845P' # nif de irlanda

    # result = email_belongs_toname("Fernando Marcos Bernabé","fernando.bernabe@i3television.es")
    # result = email_belongs_toname("Fernando Marcos Bernabé","fernando.mora@i3television.es")    
    # result = email_belongs_toname("Fernando Marcos Bernabé","soporte.comercial@i3television.es")
    # result = email_belongs_toname("Javier Bravo Benitez","javier.bravob@i3television.es")    
    # result = email_belongs_toname("Jose Antonio Alvarez de Yraola","joseantonio.yraola@atresmedia.com") 
    # result = email_belongs_toname("Manuel Torres Cambron","mtorrescam@atresadvertising.es") 
    # result = email_belongs_toname("Mª Isabel Villanego Calderon","mivillanego@atresmedia.com") 
    # result = email_belongs_toname("Javier Bravo Benitez","jbb@atresmedia.com")
    # result = email_belongs_toname("Javier Bravo Benitez","jzb@atresmedia.com")    
    # result = email_belongs_toname("Javier Bravo Benitez","jbc@atresmedia.com")

    result = email_belongs_toname('LIDIA ZORRILLA','soportesap@antena3tv.es')
    result = email_belongs_toname('PEPE DIEZ','pdiez@antena3tv.es')
    result = email_belongs_toname('PEPE DIEZ','diezp@antena3tv.es')

    #result = get_email_ok('juan.alonso@i3television.es')

    print(result)

