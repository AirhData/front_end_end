structure du projet :
/data :
    /mongodb_candidats
          - cv_parsing_agents.py : class qui va appeler le crew d'agents, afin de parser le CV                                  
                                (chaque agent a pour tache d'extraire une partie precise)
                                les données sont ensuite compilé en un fichier JSON, qui est est indexé dans la collection mongoDB,
                                elle encapsule aussi des fonctions de nettoyage et de structure du fichier.
          - mongo_utils.py : class qui regroupe les differentes etapes d'interaction avec mongodb (requete par id, insertion du document)
    /cache_api_offres.py : class qui a but mission la requete api de la base des offres, afin de les stocké en cache.

/models : 
    /crew
          - agents.py : parametrage des diferents agents utiles au projet
          - crew_pool.py : les differents crew d'agents (assemblage des agents et tasks)
          - tasks.py : listes des differentes taches attribué aux agents
    /interview simulator 
          - entretient_version_prod
            fonctionnalité centrale de l'app, le graph qui gere le chatbot avec contexte et les différents tools
- config 
  gestion de l'url de connection de la base de données ainsi que les differents prompts utilisé par le modéle (simulateur)


/prompt
  contient le prompt pour le modéle 

/static
.png et feuille de style de l'app

/templates
templates HTML du projet 

/uploads 
fichier pdf uploadé 

API nécéssaire pour faire tourner les modéles :
-GROQ 
-openai
-GOOGLE_CLIENT_ID
-LANGSMITH_API_KEY

données utilisé par les modéles :
l'extraction des données se fait par le biais d'un pipeline (orchestré par mage) pour scrapper des
des données et les stocker dans un bucket minio entre chaque etape de traitement.
les données sont ensuite embeddées et stockées dans postgreml.
Pour la version de production l'app utilise une API (contenairisé sur huggin face) qui est requeté pour recuperer les offres. 

version dev : 
/app.py
commande terminal :
python app.py

lancement de l'app en version prod : 
/app_prod.py
commande terminal : 
waitress-serve --host=127.0.0.1 --port=5000 app:app 