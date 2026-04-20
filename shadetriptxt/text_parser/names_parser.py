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
    common_forms = ["SLU", "SAU", "SL", "SA", "SRL", "SLL", "SC", "CB", "SAC", "SCA"]
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
        "Â´": "'",
        "`": "'",
        "{": "(",
        "}": ")",
        "[": "(",
        "]": ")",
        "*": " ",
        '"': " ",
        "_": " ",
        "Â·": " ",
        ",": " ",
        ";": " ",
        "|": " ",
        "\\": " ",
        "Â¬": " ",
        "â€°": " ",
        "Â½": " ",
        "Æ’": " ",
        "Å½": " ",
        "Å“": " ",
        "â€¹": " ",
        "Å ": " ",
        "Ëœ": " ",
        "â€¡": " ",
        "â€ ": " ",
        "Â¥": " ",
        "Ã°": " ",
        "Â§": " ",
        ".": " ",
    }
    for char, replacement in replace_map.items():
        oparse = oparse.replace(char, replacement)

    # Eliminar caracteres no deseados y respetar add_charset
    oparse = string_ops.erase_specialchar(oparse, add_charset)

    # Corregir caracteres en espaÃ±ol y reemplazar sÃ­mbolos
    oparse = string_ops.fix_spanish(oparse, add_charset)

    # Aplicar patrones especÃ­ficos
    oparse = symbol_pattern(oparse)
    if oparse:
        # Acomodar 'Âº' y 'Âª'
        oparse = oparse.replace("Âº", "Âº ").replace("Âª", "Âª ")
        oparse = oparse.replace(" Âº", "Âº").replace(" Âª", "Âª")

        # Normalizar segÃºn el tipo
        if format_type == "PERSONA":
            oparse = string_ops.string_aZ(oparse, "ÂºÂª" + add_charset, True)
        else:
            oparse = string_ops.string_aZ09(oparse, "ÂºÂª" + add_charset, True)

        # Eliminar espacios redundantes
        oparse = space_pattern(oparse)
        if oparse:
            oparse = oparse.replace(" + ", "+")

    return oparse.upper() if upper and oparse else oparse


def parse_company(input_string, legal_forms):
    if input_string is None:
        return input_string
    else:
        islf = -1
        comtype = None
        comname = None

        oparse = input_string.replace("(EXTINGUIDA)", "")
        oparse = oparse.replace("- EXTINGUIDA", "")
        oparse = oparse.replace("-EXTINGUIDA", "")
        oparse = oparse.replace("(EN LIQUIDACION)", "")
        oparse = oparse.replace(" EN LIQUIDACION", "")

        charset = "ÂºÂª@#$%&=+-_/\\|.:[]()Â¿?Â¡!'"
        oparse = format_name(oparse, charset, "COMPANY", True)
        if oparse:
            # check if there is a legal form
            islf = oparse.find(".")
            if islf != -1:
                islf = True
            else:
                islf = oparse.find(" ")
            if islf != -1:
                islf = True
            else:
                islf = oparse.find("(")
            if islf != -1:
                islf = True

            oparse = oparse.upper() + " "

            oparse = oparse.replace("SOCIEDAD LIMITADA", "SL")
            oparse = oparse.replace("SOCIEDAD ANONIMA", "SA")
            oparse = oparse.replace("COM PROP", "COMUNIDAD DE PROPIETARIOS")
            oparse = oparse.replace("CDAD PROP", "COMUNIDAD DE PROPIETARIOS")
            oparse = oparse.replace(" ASOC ", " ASOCIACION ")
            oparse = oparse.replace(" ASOC.", " ASOCIACION ")
            if oparse.startswith("ASOC "):
                oparse = oparse.replace("ASOC ", " ASOCIACION ")
            if oparse.startswith("ASOC."):
                oparse = oparse.replace("ASOC.", " ASOCIACION ")
            oparse = oparse.replace("SOCIEDAD DE RESPONSABILIDAD LIMITADA", "SRL")
            oparse = oparse.replace("SOCIEDAD COOPERATIVA", "SCOOP")
            oparse = oparse.replace("SOCIEDAD COOP", "SCOOP")
            oparse = oparse.replace("S COOP", "SCOOP")
            oparse = oparse.replace("SOCIEDAD ANONIMA LABORAL", "SAL")
            oparse = oparse.replace("SOCIEDAD DE RESPONSABILIDAD LIMITADA LABORAL", "SRLL")
            oparse = oparse.replace("SL LABORAL", " SLL ")
            oparse = oparse.replace("SOCIEDAD LIMITADA LABORAL", "SLL")
            oparse = oparse.replace("SA DEPORTIVA", "SAD")
            oparse = oparse.replace("SL PROFESIONAL", "SLP")

            oparse = oparse.replace(" SCOOPL", " SCOOP")
            oparse = oparse.replace(" SCL", " SC")

            if islf != -1:
                findtype = string_ops.erase_allspaces(oparse)
                findtype = findtype.replace(".", "")
                findtype = findtype.replace("(", "")
                findtype = findtype.replace(")", "")

                for form in legal_forms:
                    if findtype[-len(form) :] == form:
                        comtype = form
                        pattern = findtype.replace(comtype, "")
                        if pattern:
                            i = 0
                            comname = ""
                            for vchar in oparse:
                                comname = comname + vchar
                                if vchar == pattern[i]:
                                    i += 1
                                if i == len(pattern):
                                    break
                        break

        oparse = erase_lrspaces(oparse)

        if not comtype and oparse:
            if "COMUNIDAD DE PROPIETARIOS" in oparse:
                comtype = "COMUNIDAD DE PROPIETARIOS"
            if "COMUNIDAD DE BIENES" in oparse:
                comtype = "COMUNIDAD DE BIENES"
            if "ORGANO DE LA ADMINISTRACION" in oparse:
                comtype = "ORGANO DE LA ADMINISTRACION"
            if "ENTIDAD NO LUCRATIVA" in oparse:
                comtype = "ENTIDAD NO LUCRATIVA"
            if "CORPORACION LOCAL" in oparse:
                comtype = "CORPORACION LOCAL"
            if "SUCURSAL EN ESPAÃ‘A" in oparse:
                comtype = "SUCURSAL EN ESPAÃ‘A"
            if "PARTIDO POLITICO" in oparse:
                comtype = "PARTIDO POLITICO"
            if "ORGANISMO AUTONOMO" in oparse:
                comtype = "ORGANISMO AUTONOMO"
            if "ENTIDAD NO RESIDENTE" in oparse:
                comtype = "ENTIDAD NO RESIDENTE"
            if "ASOCIACION" in oparse:
                comtype = "ASOCIACION"
            if "ASSOCIACIO" in oparse:
                comtype = "ASOCIACION"
            if "FUNDACION" in oparse:
                comtype = "FUNDACION"

        if comtype and comname:
            return (comname, comtype)
        elif comtype:
            return (oparse, comtype)
        elif oparse:
            return (oparse, None)
        else:
            return None


def format_companyname(company_name, company_type, format):
    if company_name is None:
        return None
    else:
        comname = company_name
        if company_type:
            if company_type not in [
                "ORGANO DE LA ADMINISTRACION",
                "ENTIDAD NO LUCRATIVA",
                "CORPORACION LOCAL",
                "SUCURSAL EN ESPAÃ‘A",
                "PARTIDO POLITICO",
                "ORGANISMO AUTONOMO",
                "ENTIDAD NO RESIDENTE",
                "ASOCIACION",
                "FUNDACION",
                "CAJA",
                "MUTUA",
                "FONDO",
                "N/A",
            ]:
                if format == "brackets":
                    comtype = "(" + company_type + ")"
                elif format == "dots" or format == "comma&dots":
                    if len(company_type) >= 4 or company_type in ["LTD", "INC", "CO"]:
                        comtype = company_type + "."
                    else:
                        strtype = company_type
                        comtype = ""
                        for c in strtype:
                            comtype = comtype + c + "."

                comtype = " " + comtype
                if format == "comma&dots":
                    comtype = "," + comtype
            else:
                if company_type == "N/A":
                    comtype = ""
                else:
                    comname = get_companyname(company_name, company_type)
                    comtype = ", " + company_type
        else:
            comtype = ""

    return comname + comtype


def get_companyname(company_name, company_type):
    # comname = #'CAMINO E HIJOS CB',comtype = 'CB'
    if company_name is None:
        return None
    else:
        if company_type:
            if company_name[-len(company_type) - 1 :] == " " + company_type:
                oparse = left_replace(company_name, " " + company_type, " ")
            else:
                oparse = company_name
        else:
            oparse = company_name

        oparse = space_pattern(oparse)
        oparse = symbol_pattern(oparse)
        oparse = string_ops.flat_vowels(oparse)

        return oparse


def isformat_company(input_string):
    if input_string is None:
        return input_string
    else:
        list_companytypes = [
            "SCCIL",
            "SCCL",
            "CORP",
            "LTD",
            "INC",
            "LLC",
            "SAL",
            "SAU",
            "SLU",
            "SRL",
            "SAC",
            "SCA",
            "SLL",
            "CO",
            "LC",
            "LP",
            "AG",
            "NV",
            "SA",
            "SL",
            "SC",
            "RL",
            "CB",
            "FC",
            "S",
        ]

        return get_companytype(input_string.upper()) in list_companytypes
