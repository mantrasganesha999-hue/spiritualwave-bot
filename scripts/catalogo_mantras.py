# -*- coding: utf-8 -*-
"""Catalogo de shlokas/mantras de Ganesha (textos tradicionales) y generador de titulos, descripciones y SEO.

Reglas de honestidad (importantes para YouTube/AdSense):
  * El titulo describe EXACTAMENTE lo que el video tiene: letra + significado en pantalla.
  * Solo se dice "Mantra" cantado si existe una pista real en assets/shlokas/NN_*.mp3.
  * Sin promesas de dinero, suerte, salud ni resultados.
VERIFICA los textos con una fuente confiable (p. ej. Gita Press) antes de publicar.
"""
import os, glob, random

ENTRADAS = [
    dict(id='vakratunda', num=1, roman='Vakratunda Mahakaya', titulo_roman='Vakratunda Mahakaya Mantra',
         deva=['वक्रतुण्ड', 'महाकाय'], deva_corto='वक्रतुण्ड महाकाय', hashtag='VakratundaMahakaya',
         cards=[dict(deva=['वक्रतुण्ड महाकाय सूर्यकोटि समप्रभ ।', 'निर्विघ्नं कुरु मे देव सर्वकार्येषु सर्वदा ॥'],
                     roman=['Vakratunda Mahakaya Suryakoti Samaprabha', 'Nirvighnam Kuru Me Deva Sarvakaryeshu Sarvada'],
                     sig='O Lord of the curved trunk and mighty form, radiant as a million suns: make all my undertakings free of obstacles, always.')]),
    dict(id='shukla', num=2, roman='Shukla Ambaradharam', titulo_roman='Shukla Ambaradharam Shloka',
         deva=['शुक्लाम्बरधरं', 'विष्णुं'], deva_corto='शुक्लाम्बरधरं विष्णुं', hashtag='ShuklaAmbaradharam',
         cards=[dict(deva=['शुक्लाम्बरधरं विष्णुं शशिवर्णं चतुर्भुजम् ।', 'प्रसन्नवदनं ध्यायेत् सर्वविघ्नोपशान्तये ॥'],
                     roman=['Shuklambaradharam Vishnum Shashivarnam Chaturbhujam', 'Prasannavadanam Dhyayet Sarvavighnopashantaye'],
                     sig='We meditate on the one in white garments, all-pervading, moon-hued and four-armed, with a serene face, for the calming of all obstacles.')]),
    dict(id='gajananam', num=3, roman='Gajananam Bhootaganadi', titulo_roman='Gajananam Bhootaganadi Sevitam',
         deva=['गजाननं', 'भूतगणादिसेवितं'], deva_corto='गजाननं भूतगणादिसेवितं', hashtag='Gajananam',
         cards=[dict(deva=['गजाननं भूतगणादिसेवितं कपित्थजम्बूफलसारभक्षितम् ।', 'उमासुतं शोकविनाशकारकं नमामि विघ्नेश्वरपादपङ्कजम् ॥'],
                     roman=['Gajananam Bhootaganadi Sevitam Kapittha Jambu Phala Sara Bhakshitam', 'Umasutam Shoka Vinasha Karakam Namami Vighneshvara Pada Pankajam'],
                     sig='I bow to the lotus feet of Vighneshvara, the elephant-faced son of Uma, served by the hosts of beings and fond of the kapittha and jambu fruits.')]),
    dict(id='gayatri', num=4, roman='Ganesh Gayatri Mantra', titulo_roman='Ganesh Gayatri Mantra',
         deva=['गणेश', 'गायत्री मंत्र'], deva_corto='गणेश गायत्री मंत्र', hashtag='GaneshGayatri',
         cards=[dict(deva=['ॐ एकदन्ताय विद्महे वक्रतुण्डाय धीमहि ।', 'तन्नो दन्तिः प्रचोदयात् ॥'],
                     roman=['Om Ekadantaya Vidmahe Vakratundaya Dhimahi', 'Tanno Dantih Prachodayat'],
                     sig='We know the one-tusked Lord and meditate on the curved-trunk Lord; may Danti (Ganesha) inspire our understanding.')]),
    dict(id='omgan', num=5, roman='Om Gan Ganapataye Namaha', titulo_roman='Om Gan Ganapataye Namaha',
         deva=['ॐ गं गणपतये', 'नमः'], deva_corto='ॐ गं गणपतये नमः', hashtag='OmGanGanapatayeNamaha',
         cards=[dict(deva=['ॐ गं गणपतये नमः'], roman=['Om Gam Ganapataye Namah'],
                     sig='Salutations to Ganapati, Lord of the hosts. This mantra is often chanted in repetitions of 108.')]),
    dict(id='bappa', num=6, roman='Ganpati Bappa Morya', titulo_roman='Ganpati Bappa Morya',
         deva=['गणपति बाप्पा', 'मोरया'], deva_corto='गणपति बाप्पा मोरया', hashtag='GanpatiBappaMorya',
         cards=[dict(deva=['गणपति बाप्पा मोरया ।', 'मंगलमूर्ति मोरया ॥'], roman=['Ganapati Bappa Morya', 'Mangalmurti Morya'],
                     sig='A traditional cry of devotion to Ganpati, heard especially in Ganesh Chaturthi processions.')]),
    dict(id='aarti', num=7, roman='Jai Ganesh Deva', titulo_roman='Jai Ganesh Deva Aarti',
         deva=['जय गणेश देवा', 'आरती'], deva_corto='जय गणेश देवा आरती', hashtag='GaneshAarti',
         cards=[dict(deva=['जय गणेश जय गणेश जय गणेश देवा ।', 'माता जाकी पार्वती पिता महादेवा ॥'],
                     roman=['Jai Ganesh Jai Ganesh Jai Ganesh Deva', 'Mata Jaki Parvati Pita Mahadeva'],
                     sig='Victory to Lord Ganesha, whose mother is Parvati and whose father is Mahadeva.'),
                dict(deva=['एक दन्त दयावन्त चार भुजा धारी ।', 'माथे सिन्दूर सोहे मूस की सवारी ॥'],
                     roman=['Ek Dant Dayavant Char Bhuja Dhari', 'Mathe Sindoor Sohe Moos Ki Sawari'],
                     sig='The one-tusked, merciful, four-armed Lord, with vermilion on his forehead, riding the mouse.')]),
    dict(id='ekadantaya', num=8, roman='Ekadantaya Vakratundaya', titulo_roman='Ekadantaya Vakratundaya Mantra',
         deva=['एकदन्ताय', 'वक्रतुण्डाय'], deva_corto='एकदन्ताय वक्रतुण्डाय', hashtag='Ekadantaya',
         cards=[dict(deva=['एकदन्ताय वक्रतुण्डाय गौरीतनयाय धीमहि ।', 'गजेशानाय भालचन्द्राय श्रीगणेशाय धीमहि ॥'],
                     roman=['Ekadantaya Vakratundaya Gauri Tanayaya Dhimahi', 'Gajeshanaya Bhalachandraya Shri Ganeshaya Dhimahi'],
                     sig='We meditate on Shri Ganesha: one-tusked, curved-trunked son of Gauri, Lord of elephants, wearing the moon on his forehead.')]),
    dict(id='nombres', num=9, roman='12 Names of Ganesha', titulo_roman='12 Names of Ganesha',
         deva=['गणेश के', '१२ नाम'], deva_corto='गणेश के १२ नाम', hashtag='GaneshNames',
         cards=[dict(deva=['सुमुखश्चैकदन्तश्च कपिलो गजकर्णकः ।', 'लम्बोदरश्च विकटो विघ्ननाशो विनायकः ॥'],
                     roman=['Sumukhashchaikadantashcha Kapilo Gajakarnakah', 'Lambodarashcha Vikato Vighnanasho Vinayakah'],
                     sig='Names of Ganesha: Sumukha, Ekadanta, Kapila, Gajakarnaka, Lambodara, Vikata, Vighnanasha and Vinayaka.'),
                dict(deva=['धूम्रकेतुर्गणाध्यक्षो भालचन्द्रो गजाननः ।'],
                     roman=['Dhumraketurganadhyaksho Bhalachandro Gajananah'],
                     sig='More names: Dhumraketu, Ganadhyaksha, Bhalachandra and Gajanana.')]),
    dict(id='dhyana', num=10, roman='Ekadantam Mahakayam', titulo_roman='Ganesh Dhyana Shloka',
         deva=['गणेश ध्यान', 'श्लोक'], deva_corto='गणेश ध्यान श्लोक', hashtag='GaneshDhyana',
         cards=[dict(deva=['एकदन्तं महाकायं तप्तकाञ्चनसन्निभम् ।', 'लम्बोदरं विशालाक्षं वन्देऽहं गणनायकम् ॥'],
                     roman=['Ekadantam Mahakayam Taptakanchana Sannibham', 'Lambodaram Vishalaksham Vande Aham Gananayakam'],
                     sig='I bow to the leader of the hosts: one-tusked, large-bodied, glowing like molten gold, big-bellied and wide-eyed.')]),
    dict(id='mushika', num=11, roman='Mushika Vahana Modaka Hasta', titulo_roman='Mushika Vahana Modaka Hasta',
         deva=['मूषकवाहन', 'मोदकहस्त'], deva_corto='मूषकवाहन मोदकहस्त', hashtag='MushikaVahana',
         cards=[dict(deva=['मूषकवाहन मोदकहस्त चामरकर्ण विलम्बितसूत्र ।', 'वामनरूप महेश्वरपुत्र विघ्नविनायक पाद नमस्ते ॥'],
                     roman=['Mushika Vahana Modaka Hasta Chamara Karna Vilambita Sutra', 'Vamana Rupa Maheshvara Putra Vighna Vinayaka Pada Namaste'],
                     sig='Salutations at the feet of Vighna Vinayaka, son of Maheshvara, who rides a mouse, holds sweets in hand and has ears like fans.')]),
    dict(id='shriganesh', num=12, roman='Om Shri Ganeshaya Namah', titulo_roman='Om Shri Ganeshaya Namah',
         deva=['ॐ श्री गणेशाय', 'नमः'], deva_corto='ॐ श्री गणेशाय नमः', hashtag='ShriGaneshayaNamah',
         cards=[dict(deva=['ॐ श्री गणेशाय नमः'], roman=['Om Shri Ganeshaya Namah'],
                     sig='Salutations to Shri Ganesha, traditionally invoked at the start of any new work or study.')]),
    dict(id='vighneshwara', num=13, roman='Om Vighneshwaraya Namah', titulo_roman='Om Vighneshwaraya Namah',
         deva=['ॐ विघ्नेश्वराय', 'नमः'], deva_corto='ॐ विघ्नेश्वराय नमः', hashtag='Vighneshwara',
         cards=[dict(deva=['ॐ विघ्नेश्वराय नमः'], roman=['Om Vighneshvaraya Namah'],
                     sig='Salutations to Vighneshvara, the Lord of obstacles, one of the best-known names of Ganesha.')]),
]
POR_ID = {e['id']: e for e in ENTRADAS}


def entrada_por_id(i):
    return POR_ID[i]


def pistas_shloka(base, entrada):
    """Pistas reales cantadas para este shloka (assets/shlokas/NN_*.mp3). Lista vacia si no hay."""
    carpeta = os.path.join(base, 'assets', 'shlokas')
    return sorted(glob.glob(os.path.join(carpeta, f"{entrada['num']:02d}_*.mp3")))


def _recortar(texto, maximo):
    if len(texto) <= maximo:
        return texto
    return texto[:maximo].rsplit(' ', 1)[0].rstrip(' |,-')


def textos_completos(entrada):
    deva = [l for c in entrada['cards'] for l in c['deva']]
    roman = [l for c in entrada['cards'] for l in c['roman']]
    sig = ' '.join(c['sig'] for c in entrada['cards'])
    return deva, roman, sig


def _descripcion(entrada, idioma, cantado, es_short, hashtags):
    deva, roman, sig = textos_completos(entrada)
    if cantado:
        intro = f"{entrada['titulo_roman']}: chanted mantra with lyrics in Devanagari, transliteration and English meaning."
        musica = "Audio: a devotional chant of this text created with AI music tools."
    else:
        intro = (f"{entrada['titulo_roman']}: lyrics in Devanagari, transliteration and English meaning, "
                 "shown on screen with devotional Ganesha music so you can read along.")
        musica = "Audio: devotional Ganesha music created with AI tools (the music is not a recitation of this text)."
    partes = [intro, "", "\n".join(deva), "", "\n".join(roman), "", "Meaning: " + sig, ""]
    if not es_short:
        partes += ["About: Ganesha (Ganpati, Vighnaharta) is traditionally invoked at the start of new beginnings. "
                   "This video is made for devotion, reading along and quiet reflection.", ""]
    partes += [musica, "",
               "जय गणेश! चैनल को सब्सक्राइब करें।" if idioma == 'hi' else "Jai Ganesh! Subscribe for more.",
               "Subscribe: youtube.com/@SpiritualWave888", "",
               hashtags, "",
               "The music, images and videos were created with artificial intelligence tools."]
    return "\n".join(partes)[:4800]


def _hashtags(entrada, idioma, es_short):
    base = ['#Ganesha', '#GaneshMantra', '#Ganpati']
    extra = ['#' + entrada['hashtag']]
    if es_short:
        extra.append('#Shorts')
    return ' '.join((extra + base)[:5])


def _tags_extra(entrada):
    r = entrada['roman'].lower()
    return [f"{r} mantra", f"{r} lyrics", entrada['deva_corto'], 'ganesh mantra lyrics',
            'ganesh mantra with meaning', 'ganpati bappa', 'ganesha devotional', 'ganesh aarti' if entrada['id'] == 'aarti' else 'ganesh shloka']


def meta_largo(entrada, idioma, cantado):
    if cantado:
        titulo = f"{entrada['titulo_roman']} | {entrada['deva_corto']} | Lyrics & Meaning"
        sub = random.choice(['CHANT + LYRICS', 'MANTRA + MEANING'])
    else:
        titulo = f"{entrada['titulo_roman']} Lyrics & Meaning | {entrada['deva_corto']} | Ganesha"
        sub = random.choice(['LYRICS + MEANING', 'WITH LYRICS', 'LYRICS • MEANING'])
    titulo = _recortar(titulo, 100)
    hashtags = _hashtags(entrada, idioma, False)
    return dict(titulo=titulo, descripcion=_descripcion(entrada, idioma, cantado, False, hashtags),
                hashtags=hashtags, sub=sub, badge=random.choice(['HD', 'HD', 'NEW']), tags_extra=_tags_extra(entrada))


def meta_short(entrada, idioma, cantado):
    titulo = _recortar(f"{entrada['deva_corto']} | {entrada['roman']} lyrics", 90)
    hashtags = _hashtags(entrada, idioma, True)
    return dict(titulo=titulo, descripcion=_descripcion(entrada, idioma, cantado, True, hashtags),
                hashtags=hashtags, sub='LYRICS + MEANING' if not cantado else 'CHANT + LYRICS',
                badge=random.choice(['HD', 'NEW']), tags_extra=_tags_extra(entrada))
