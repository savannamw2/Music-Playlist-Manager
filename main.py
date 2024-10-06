
from flask import Flask, request, jsonify
from fire_config import db, auth
from firebase_admin import firestore

app = Flask(__name__)

# Add a root route


@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Music Playlist Manager API"}), 200


# Helper function to validate Firebase ID Tokens


def verify_token(id_token):
    try:
        decoded_token = auth.get_account_info(id_token)
        return decoded_token['users'][0]['localId']
    except:
        return None

# User Sign Up


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    display_name = data.get('display_name', '')

    try:
        user = auth.create_user_with_email_and_password(email, password)
        user_id = user['localId']
        # Save additional user info in Firestore
        db.collection('Users').document(user_id).set({
            'email': email,
            'display_name': display_name
        })
        return jsonify({"message": "User created successfully", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# User Sign In


@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        user = auth.sign_in_with_email_and_password(email, password)
        id_token = user['idToken']
        return jsonify({"message": "Signed in successfully", "id_token": id_token}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Create a Playlist


@app.route('/playlists', methods=['POST'])
def create_playlist():
    id_token = request.headers.get('Authorization')
    user_id = verify_token(id_token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    songs = data.get('songs', [])  # List of song dictionaries

    if not name:
        return jsonify({"error": "Playlist name is required"}), 400

    playlist_ref = db.collection('Playlists').document()
    playlist_ref.set({
        'name': name,
        'description': description,
        'owner_id': user_id,
        'shared_with': [],
        'songs': songs
    })

    return jsonify({"message": "Playlist created successfully", "playlist_id": playlist_ref.id}), 201

# Get User's Playlists


@app.route('/playlists', methods=['GET'])
def get_playlists():
    id_token = request.headers.get('Authorization')
    user_id = verify_token(id_token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    playlists = db.collection('Playlists')\
                  .where('owner_id', '==', user_id)\
                  .stream()

    result = []
    for playlist in playlists:
        data = playlist.to_dict()
        data['playlist_id'] = playlist.id
        result.append(data)

    return jsonify({"playlists": result}), 200

# Update a Playlist


@app.route('/playlists/<playlist_id>', methods=['PUT'])
def update_playlist(playlist_id):
    id_token = request.headers.get('Authorization')
    user_id = verify_token(id_token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    playlist_ref = db.collection('Playlists').document(playlist_id)
    playlist = playlist_ref.get()
    if not playlist.exists:
        return jsonify({"error": "Playlist not found"}), 404

    if playlist.to_dict().get('owner_id') != user_id:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    songs = data.get('songs')

    update_data = {}
    if name:
        update_data['name'] = name
    if description:
        update_data['description'] = description
    if songs is not None:
        update_data['songs'] = songs

    if update_data:
        playlist_ref.update(update_data)
        return jsonify({"message": "Playlist updated successfully"}), 200
    else:
        return jsonify({"message": "No updates provided"}), 400

# Delete a Playlist


@app.route('/playlists/<playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    id_token = request.headers.get('Authorization')
    user_id = verify_token(id_token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    playlist_ref = db.collection('Playlists').document(playlist_id)
    playlist = playlist_ref.get()
    if not playlist.exists:
        return jsonify({"error": "Playlist not found"}), 404

    if playlist.to_dict().get('owner_id') != user_id:
        return jsonify({"error": "Forbidden"}), 403

    playlist_ref.delete()
    return jsonify({"message": "Playlist deleted successfully"}), 200

# Share a Playlist


@app.route('/playlists/<playlist_id>/share', methods=['POST'])
def share_playlist(playlist_id):
    id_token = request.headers.get('Authorization')
    user_id = verify_token(id_token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    playlist_ref = db.collection('Playlists').document(playlist_id)
    playlist = playlist_ref.get()
    if not playlist.exists:
        return jsonify({"error": "Playlist not found"}), 404

    if playlist.to_dict().get('owner_id') != user_id:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    shared_with = data.get('shared_with')  # List of user_ids

    if not isinstance(shared_with, list):
        return jsonify({"error": "shared_with must be a list of user_ids"}), 400

    playlist_ref.update({
        'shared_with': firestore.ArrayUnion(shared_with)
    })

    return jsonify({"message": "Playlist shared successfully"}), 200

# Get Shared Playlists


@app.route('/shared_playlists', methods=['GET'])
def get_shared_playlists():
    id_token = request.headers.get('Authorization')
    user_id = verify_token(id_token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    playlists = db.collection('Playlists')\
                  .where('shared_with', 'array_contains', user_id)\
                  .stream()

    result = []
    for playlist in playlists:
        data = playlist.to_dict()
        data['playlist_id'] = playlist.id
        result.append(data)

    return jsonify({"shared_playlists": result}), 200


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
