# backend_app.py
from flask import Flask, request, jsonify, abort
from ultralytics import YOLO
import rasterio
import os
import werkzeug.utils

app = Flask(__name__)

# Tenta carregar o modelo. Se falhar, a aplicação não iniciará, o que é bom para depuração.
try:
    print("Carregando o modelo YOLOv8...")
    model = YOLO('best.pt') 
    print("✅ Modelo carregado com sucesso.")
except Exception as e:
    print(f"❌ Erro fatal ao carregar o modelo: {e}")
    # Impede que a aplicação continue se o modelo não puder ser carregado.
    raise e

# --- NOVA ROTA DE HEALTH CHECK ---
# Responde a pedidos na raiz da URL para dizer ao Cloud Run que o serviço está saudável.
@app.route('/', methods=['GET'])
def health_check():
    return "Backend do Detector de Hotspots está online e pronto para receber análises no endpoint /analyze_geotiff.", 200

@app.route('/analyze_geotiff', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        abort(400, description="Nenhum arquivo enviado.")
    
    file = request.files['file']
    if file.filename == '':
        abort(400, description="Nenhum arquivo selecionado.")

    filename = werkzeug.utils.secure_filename(file.filename)
    temp_path = os.path.join("./", filename)
    file.save(temp_path)

    print(f"Analisando o arquivo: {filename}")
    detections_data = []
    
    try:
        results = model(temp_path)
        with rasterio.open(temp_path) as src:
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = [int(i) for i in box.xyxy[0]]
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    lon, lat = src.transform * (center_x, center_y)
                    
                    detections_data.append({
                        'tipo_falha': model.names[int(box.cls[0])],
                        'confianca': f"{float(box.conf[0]):.2%}",
                        'latitude': lat,
                        'longitude': lon
                    })
        print(f"✅ Análise concluída. {len(detections_data)} falhas encontradas.")
    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")
        abort(500, description="Erro ao processar o arquivo de imagem.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return jsonify(detections_data)

if __name__ == '__main__':
    # Esta parte é para testes locais. O Gunicorn, usado na produção, ignora isto.
    app.run(host='0.0.0.0', port=8080)
