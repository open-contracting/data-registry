# Generated by Django 3.2.16 on 2023-03-09 21:32

from django.db import migrations


def update_country_flag_name(apps, schema_editor):
    # Only for currently existing countries flags in the database
    mapping = {
        "afghanistan.png": "af.svg",
        "argentina.png": "ar.svg",
        "australia.png": "au.svg",
        "austria.png": "at.svg",
        "belgium.png": "be.svg",
        "bolivia.png": "bo.svg",
        "bulgaria.png": "bg.svg",
        "canada.png": "ca.svg",
        "chile.png": "cl.svg",
        "colombia.png": "co.svg",
        "costa-rica.png": "cr.svg",
        "croatia.png": "hr.svg",
        "cyprus.png": "cy.svg",
        "czech-republic.png": "cz.svg",
        "denmark.png": "dk.svg",
        "dominican-republic.png": "do.svg",
        "ecuador.png": "ec.svg",
        "estonia.png": "ee.svg",
        "european-union.png": "eu.svg",
        "finland.png": "fi.svg",
        "france.png": "fr.svg",
        "georgia.png": "ge.svg",
        "germany.png": "de.svg",
        "ghana.png": "gh.svg",
        "greece.png": "gr.svg",
        "honduras.png": "hn.svg",
        "hungary.png": "hu.svg",
        "iceland.png": "is.svg",
        "india.png": "in.svg",
        "indonesia.png": "id.svg",
        "ireland.png": "ie.svg",
        "italy.png": "it.svg",
        "kenya.png": "ke.svg",
        "kosovo.png": "xk.svg",
        "kyrgyzstan.png": "kg.svg",
        "latvia.png": "lv.svg",
        "lithuania.png": "lt.svg",
        "luxembourg.png": "lu.svg",
        "malta.png": "mt.svg",
        "mexico.png": "mx.svg",
        "moldova.png": "md.svg",
        "nepal.png": "np.svg",
        "netherlands.png": "nl.svg",
        "nigeria.png": "ng.svg",
        "norway.png": "no.svg",
        "pakistan.png": "pk.svg",
        "panama.png": "pa.svg",
        "paraguay.png": "py.svg",
        "peru.png": "pe.svg",
        "poland.png": "pl.svg",
        "portugal.png": "pt.svg",
        "romania.png": "ro.svg",
        "slovakia.png": "sk.svg",
        "slovenia.png": "si.svg",
        "spain.png": "es.svg",
        "sweden.png": "se.svg",
        "switzerland.png": "ch.svg",
        "tanzania.png": "tz.svg",
        "uganda.png": "ug.svg",
        "united-kingdom.png": "gb.svg",
        "uruguay.png": "uy.svg",
        "zambia.png": "zm.svg",
    }
    Collection = apps.get_model("data_registry", "Collection")
    for collection in Collection.objects.all():
        if collection.country_flag:
            collection.country_flag = mapping[collection.country_flag]
            collection.save()


class Migration(migrations.Migration):
    dependencies = [
        ("data_registry", "0038_auto_20220923_0259"),
    ]

    operations = [
        migrations.RunPython(update_country_flag_name),
    ]
