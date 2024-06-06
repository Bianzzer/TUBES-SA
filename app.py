from flask import Flask, request, jsonify, render_template
import random
import math
import itertools

app = Flask(__name__)

# Fungsi untuk menghasilkan desa dengan koordinat acak
def generate_villages(num_villages):
    coords = [(i * 10, i * 10) for i in range(num_villages)]
    return [(f"desa {i+1}", coords[i]) for i in range(num_villages)]

# Fungsi untuk menghitung jarak antara dua koordinat
def calculate_distance(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)

# Fungsi untuk membuat matriks jarak menggunakan data yang telah diberikan
def create_fixed_distance_matrix():
    distance_matrix = [
        [0, 5, 7, 3, 6, 8, 2, 4, 9, 10],
        [5, 0, 2, 6, 4, 7, 9, 1, 8, 3],
        [7, 2, 0, 8, 5, 3, 6, 4, 10, 2],
        [3, 6, 8, 0, 7, 4, 5, 2, 6, 9],
        [6, 4, 5, 7, 0, 3, 10, 5, 8, 1],
        [8, 7, 3, 4, 3, 0, 2, 6, 5, 7],
        [2, 9, 6, 5, 10, 2, 0, 8, 4, 3],
        [4, 1, 4, 2, 5, 6, 8, 0, 7, 9],
        [9, 8, 10, 6, 8, 5, 4, 7, 0, 2],
        [10, 3, 2, 9, 1, 7, 3, 9, 2, 0]
    ]
    return distance_matrix

# Fungsi untuk membuat jalur tetap
def fixed_path(num_villages):
    fixed_order = [0, 2, 7, 3, 4, 1, 5, 6, 8, 9]  # Urutan tetap untuk maksimal 10 desa
    return fixed_order[:num_villages] + [0]  # Mengembalikan jalur yang sesuai dengan jumlah desa

# Algoritma Greedy TSP berdasarkan jarak terdekat
def greedy_tsp(villages, distance_matrix):
    num_villages = len(villages)
    unvisited = list(range(num_villages))
    current = unvisited.pop(0)
    path = [current]

    while unvisited:
        next_village = min(unvisited, key=lambda x: distance_matrix[current][x])
        unvisited.remove(next_village)
        path.append(next_village)
        current = next_village

    path.append(path[0])  # Kembali ke desa awal
    steps = [f"Pindah dari {villages[path[i]][0]} ke {villages[path[i+1]][0]}" for i in range(len(path)-1)]
    return path, steps

# Algoritma Brute Force TSP
def brute_force_tsp(villages, distance_matrix):
    steps = []
    num_villages = len(villages)
    all_permutations = itertools.permutations(range(1, num_villages))
    min_path = None
    min_distance = float('inf')

    steps.append("Menghasilkan semua kemungkinan jalur:")
    for perm in all_permutations:
        current_path = [0] + list(perm) + [0]
        current_distance = sum(distance_matrix[current_path[i]][current_path[i+1]] for i in range(num_villages))
        steps.append(f"Jalur: {' -> '.join(villages[i][0] for i in current_path)} dengan jarak {current_distance:.2f}")
        
        if current_distance < min_distance:
            min_distance = current_distance
            min_path = current_path

    steps.append(f"Jalur terpendek adalah: {' -> '.join(villages[i][0] for i in min_path)} dengan jarak {min_distance:.2f}")
    return min_path, steps

@app.route('/')
def index():
    # Render halaman index.html
    return render_template('index.html')

@app.route('/identify', methods=['POST'])
def identify():
    data = request.get_json()
    player_names = data.get('players')
    num_werewolves = int(data.get('num_werewolves'))
    method = data.get('method')

    if len(player_names) < 4:
        return jsonify({"error": "Jumlah pemain tidak boleh kurang dari 4"}), 400
    
    if len(player_names) > 10:
        return jsonify({"error": "Jumlah pemain tidak boleh lebih dari 10"}), 400
    
    max_werewolves = len(player_names) // 2
    if num_werewolves > max_werewolves:
        return jsonify({"error": f"Melebihi batas maksimum werewolf"}), 400

    # Menghasilkan 6-10 desa secara default
    num_villages = max(random.randint(6, 10), len(player_names))
    villages = generate_villages(num_villages)
    distance_matrix = create_fixed_distance_matrix()

    # Memilih algoritma TSP berdasarkan metode yang dipilih
    if method == 'greedy':
        werewolf_path, algorithm_steps = greedy_tsp(villages, distance_matrix)
    elif method == 'brute_force':
        werewolf_path, algorithm_steps = brute_force_tsp(villages, distance_matrix)
    else:
        werewolf_path = []
        algorithm_steps = []

    # Menghitung waktu tempuh untuk werewolf (menggunakan jalur tetap)
    werewolf_distance = sum(distance_matrix[werewolf_path[i]][werewolf_path[i+1]] for i in range(len(werewolf_path) - 1))

    # Mengidentifikasi werewolf secara acak dari nama pemain
    identified_werewolves = random.sample(player_names, num_werewolves)
    steps = []

    # Menghasilkan langkah-langkah untuk werewolf
    remaining_players = player_names[:]
    for player in identified_werewolves:
        player_steps = f"Pemain {player} mengunjungi desa dengan urutan: {' -> '.join(villages[i][0] for i in werewolf_path)} dengan jarak {werewolf_distance:.2f} km"
        steps.append(player_steps)
        remaining_players.remove(player)

    # Menghasilkan langkah-langkah untuk pemain lainnya
    villager_paths = {}
    for player in remaining_players:
        random_path = list(range(1, num_villages))
        random.shuffle(random_path)
        random_path = [0] + random_path + [0]
        villager_paths[player] = random_path
        villager_distance = sum(distance_matrix[random_path[i]][random_path[i+1]] for i in range(len(random_path) - 1))
        player_steps = f"Pemain {player} mengunjungi desa dengan urutan: {' -> '.join(villages[i][0] for i in random_path)} dengan jarak {villager_distance:.2f} km"
        steps.append(player_steps)

    # Menghitung waktu tempuh untuk villager dan mengidentifikasi
    villager_identification = {}
    for player, v_path in villager_paths.items():
        villager_distance = sum(distance_matrix[v_path[i]][v_path[i+1]] for i in range(len(v_path) - 1))
        if villager_distance > werewolf_distance:
            villager_identification[player] = "Villager"
        else:
            villager_identification[player] = "Werewolf"

    # Mengembalikan hasil dalam format JSON
    result = {
        'path': [villages[i][0] for i in werewolf_path],
        'identified_werewolves': identified_werewolves,
        'steps': steps,
        'algorithm_steps': algorithm_steps,
        'shortest_path': [villages[i][0] for i in werewolf_path],
        'villager_identification': villager_identification
    }
    return jsonify(result)

if __name__ == '__main__':
    # Menjalankan aplikasi Flask dalam mode debug
    app.run(debug=True)
