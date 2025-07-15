@app.route('/interview-ai', methods=['GET', 'POST'])
@login_required
def interview_ai():
    MODEL_API_URL = Config.MODEL_API_URL
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            messages_from_client = data.get('messages', [])
            job_id = data.get('job_id')

            if not job_id:
                return jsonify({'error': 'Donnée manquante : job_id'}), 400
            
            # Validation des messages
            if not isinstance(messages_from_client, list):
                return jsonify({'error': 'Messages invalides'}), 400
            
            for msg in messages_from_client:
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    return jsonify({'error': 'Format de message invalide'}), 400
            
            mongo_manager = MongoManager()
            
            # Vérification du CV
            if not g.user.candidate_mongo_id:
                mongo_manager.close_connection()
                return jsonify({'error': 'Aucun CV trouvé. Veuillez d\'abord télécharger un CV.'}), 400
            
            cv_document = mongo_manager.get_profile_by_id(g.user.candidate_mongo_id)
            if not cv_document:
                mongo_manager.close_connection()
                return jsonify({'error': 'CV introuvable dans la base de données.'}), 400

            # Récupération de l'offre d'emploi
            jobs = fetch_job_offers()
            job_offer = next((job for job in jobs if job.get('id') == job_id), None)
            if not job_offer:
                mongo_manager.close_connection()
                return jsonify({'error': 'Offre d\'emploi introuvable.'}), 404

            # Formatage de l'offre d'emploi
            job_offer_formatted = {
                "entreprise": job_offer.get("entreprise", "Entreprise non spécifiée"),
                "poste": job_offer.get("poste", "Poste non spécifié"),
                "description": job_offer.get("description_poste", job_offer.get("description", "Description non disponible")),
                "mission": job_offer.get("mission", job_offer.get("description", "Mission non spécifiée")),
                "pole": job_offer.get("pole", job_offer.get("departement", "Pôle non spécifié")),
                "profil_recherche": job_offer.get("profil_recherche", "Profil recherché non spécifié"),
                "competences": job_offer.get("competences", job_offer.get("skills_required", "Compétences non spécifiées"))
            }
            
            # Récupération de l'historique de conversation
            conversation_history = mongo_manager.get_conversation_history(g.user.google_id, job_id) or []
            
            # Préparation du payload - structure simplifiée
            payload = {
                "user_id": g.user.google_id,
                "job_offer_id": job_id,
                "cv_document": cv_document,
                "job_offer": job_offer_formatted,
                "messages": messages_from_client,
                "conversation_history": conversation_history  # Historique séparé
            }
            
            # Ajout de logs pour debugging
            logging.info(f"Envoi de la requête à l'API pour l'utilisateur {g.user.google_id}")
            logging.debug(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            # Appel à l'API
            api_response = requests.post(
                f"{MODEL_API_URL}/simulate-interview/",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30  # Timeout de 30 secondes
            )
            
            # Vérification de la réponse
            if api_response.status_code != 200:
                logging.error(f"Erreur API {api_response.status_code}: {api_response.text}")
                mongo_manager.close_connection()
                return jsonify({'error': f'Erreur API: {api_response.status_code}'}), 500
            
            response_data = api_response.json()
            ai_message = response_data.get("response", "Désolé, je n'ai pas pu traiter votre demande.")

            # Mise à jour de l'historique
            updated_history = messages_from_client + [{"role": "assistant", "content": ai_message}]
            mongo_manager.save_conversation_history(g.user.google_id, job_id, updated_history)
            
            mongo_manager.close_connection()
            return jsonify({"response": ai_message})

        except requests.exceptions.Timeout:
            logging.error("Timeout lors de l'appel à l'API")
            return jsonify({'error': 'Le service d\'entretien IA a mis trop de temps à répondre.'}), 504
        
        except requests.exceptions.ConnectionError:
            logging.error("Erreur de connexion à l'API")
            return jsonify({'error': 'Impossible de contacter le service d\'entretien IA.'}), 503
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur de communication avec l'API: {e}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Réponse de l'API: {e.response.text}")
            return jsonify({'error': 'Erreur de communication avec l\'assistant IA.'}), 500
        
        except json.JSONDecodeError:
            logging.error("Erreur de parsing JSON de la réponse API")
            return jsonify({'error': 'Réponse invalide de l\'assistant IA.'}), 500
        
        except Exception as e:
            error_details = traceback.format_exc()
            logging.error(f"Erreur critique dans POST /interview-ai: {error_details}")
            return jsonify({'error': 'Une erreur interne est survenue.'}), 500
        
        finally:
            # S'assurer que la connexion MongoDB est fermée
            try:
                if 'mongo_manager' in locals():
                    mongo_manager.close_connection()
            except:
                pass

    # Partie GET reste identique
    try:
        job_id = request.args.get('job_id')
        if not job_id:
            flash("Aucune offre d'emploi sélectionnée.", "warning")
            return redirect(url_for('jobs'))
        
        jobs = fetch_job_offers()
        job_offer = next((job for job in jobs if job.get('id') == job_id), None)
        if not job_offer:
            flash("L'offre d'emploi sélectionnée est introuvable.", "danger")
            return redirect(url_for('jobs'))
            
        mongo_manager = MongoManager()
        mongo_manager.delete_conversation_history(g.user.google_id, job_id)
        mongo_manager.close_connection()
        
        return render_template('interview_ai.html', job_offer=job_offer, config=Config)
    
    except Exception as e:
        error_details = traceback.format_exc()
        logging.error(f"Erreur critique dans GET /interview-ai: {error_details}")
        flash("Une erreur interne est survenue lors du chargement de la page d'entretien.", "danger")
        return redirect(url_for('home'))
