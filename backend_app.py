from flask import Flask, request, jsonify, abort
from ultralytics import YOLO
import rasterio
import os
import sys
import traceback
import werkzeug.utils
from werkzeug.exceptions import RequestEntityTooLarge

# Configuração da aplicação Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Variável global para o modelo
model = None

def load_model():
    """Carrega o modelo YOLO de forma segura"""
    global model
    try:
        print("🔄 Carregando o modelo YOLOv8...")
        if not os.path.exists('best.pt'):
            print("❌ Arquivo best.pt não encontrado!")
            return False
        
        model = YOLO('best.pt')
        print("✅ Modelo carregado com sucesso.")
        return True
    except Exception as e:
        print(f"❌ Erro ao carregar o modelo: {e}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        return False

# Carrega o modelo na inicialização
model_loaded = load_model()

@app.route('/', methods=['GET'])
def health_check():
    """Endpoint de health check para o Cloud Run"""
    status = {
        'status': 'online',
        'message': 'Backend do Detector de Hotspots está funcionando',
        'modelo_carregado': model is not None
    }
    return jsonify(status), 200

@app.route('/status', methods=['GET'])
def status():
    """Endpoint para verificar o status detalhado do serviço"""
    return jsonify({
        'service': 'Detector de Hotspots Backend',
        'status': 'running',
        'model_loaded': model is not None,
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Health check'},
            {'path': '/status', 'method': 'GET', 'description': 'Status detalhado'},
            {'path': '/analyze_geotiff', 'method': 'POST', 'description': 'Análise de imagens GeoTIFF'}
        ]
    }), 200

@app.route('/analyze_geotiff', methods=['POST'])
def analyze():
    """Endpoint principal para análise de imagens GeoTIFF"""
    # Verifica se o modelo foi carregado
    if not model_loaded or model is None:
        return jsonify({
            'error': 'Modelo não carregado. Serviço indisponível.',
            'codigo': 'MODEL_NOT_LOADED'
        }), 503
    
    # Verifica se um arquivo foi enviado
    if 'file' not in request.files:
        return jsonify({
            'error': 'Nenhum arquivo enviado.',
            'codigo': 'NO_FILE'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'error': 'Nenhum arquivo selecionado.',
            'codigo': 'EMPTY_FILENAME'
        }), 400
    
    # Salva o arquivo temporariamente
    filename = werkzeug.utils.secure_filename(file.filename)
    temp_path = os.path.join("/tmp", filename)
    
    try:
        file.save(temp_path)
        print(f"📁 Arquivo salvo: {filename} ({os.path.getsize(temp_path)} bytes)")
        
        # Executa a análise
        detections_data = []
        
        print("🔍 Iniciando análise com YOLO...")
        results = model(temp_path)
        
        print("🗺️ Processando coordenadas geográficas...")
        with rasterio.open(temp_path) as src:
            print(f"📊 Dimensões da imagem: {src.width}x{src.height}")
            print(f"🌍 Sistema de coordenadas: {src.crs}")
            
            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        x1, y1, x2, y2 = [int(i) for i in box.xyxy[0]]
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        
                        # Converte coordenadas pixel para coordenadas geográficas
                        lon, lat = src.transform * (center_x, center_y)
                        
                        detections_data.append({
                            'tipo_falha': model.names[int(box.cls[0])],
                            'confianca': f"{float(box.conf[0]):.2%}",
                            'latitude': float(lat),
                            'longitude': float(lon),
                            'bbox': {
                                'x1': int(x1), 'y1': int(y1),
                                'x2': int(x2), 'y2': int(y2)
                            }
                        })
        
        print(f"✅ Análise concluída. {len(detections_data)} detecções encontradas.")
        
        return jsonify({
            'success': True,
            'deteccoes': detections_data,
            'total_deteccoes': len(detections_data),
            'arquivo_analisado': filename
        }), 200
        
    except RequestEntityTooLarge:
        return jsonify({
            'error': 'Arquivo muito grande. Máximo permitido: 100MB',
            'codigo': 'FILE_TOO_LARGE'
        }), 413
        
    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        
        return jsonify({
            'error': 'Erro interno durante o processamento',
            'codigo': 'PROCESSING_ERROR',
            'detalhes': str(e)
        }), 500
        
    finally:
        # Remove o arquivo temporário
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"🗑️ Arquivo temporário removido: {temp_path}")
            except Exception as e:
                print(f"⚠️ Erro ao remover arquivo temporário: {e}")

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint não encontrado',
        'codigo': 'NOT_FOUND',
        'endpoints_disponiveis': ['/', '/status', '/analyze_geotiff']
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Erro interno do servidor',
        'codigo': 'INTERNAL_ERROR'
    }), 500

if __name__ == '__main__':
    # Para desenvolvimento local
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
