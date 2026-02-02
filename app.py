from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red
from io import BytesIO
import os
import zipfile
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_position(width, height, position, x_offset, y_offset, font_size, text="Made in China"):
    text_width = len(text) * font_size * 0.6
    margin = 10 + font_size
    
    position_map = {
        "top-left": (margin, height - margin),
        "top-center": ((width - text_width) / 2, height - margin),
        "top-right": (width - text_width - margin, height - margin),
        "middle-left": (margin, height / 2),
        "center": ((width - text_width) / 2, height / 2),
        "middle-right": (width - text_width - margin, height / 2),
        "bottom-left": (margin, margin),
        "bottom-center": ((width - text_width) / 2, margin),
        "bottom-right": (width - text_width - margin, margin),
    }
    
    x, y = position_map.get(position, position_map["top-right"])
    x += x_offset
    y += y_offset  # For bottom positions, positive y_offset moves up, negative moves down
    
    # Ensure the label stays within bounds
    x = max(margin, min(x, width - text_width - margin))
    y = max(margin, min(y, height - margin - font_size))  # Ensure enough space for the text
    
    return x, y

def add_label_to_pdf(input_stream, position, x_offset, y_offset, font_size, font_color, label_text="Made in China"):
    reader = PdfReader(input_stream)
    writer = PdfWriter()
    
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        
        x, y = calculate_position(width, height, position, x_offset, y_offset, font_size, label_text)
        
        # Create a temporary PDF with the label
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        can.setFont("Helvetica", font_size)
        
        # Parse hex color
        if font_color.startswith('#'):
            font_color = font_color[1:]
        r = int(font_color[:2], 16) / 255.0
        g = int(font_color[2:4], 16) / 255.0
        b = int(font_color[4:6], 16) / 255.0
        can.setFillColorRGB(r, g, b)
        
        can.drawString(x, y, label_text)
        can.save()
        
        # Move to the beginning of the StringIO buffer
        packet.seek(0)
        
        # Merge the label with the original page
        overlay_pdf = PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)
    
    output_stream = BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    
    return output_stream

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF标签添加工具 - 生产版</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input, select {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            button {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #0056b3;
            }
            .result {
                margin-top: 20px;
                padding: 10px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                display: none;
            }
            .instructions {
                background-color: #e7f3fe;
                border: 1px solid #b3d9ff;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 PDF标签添加工具</h1>
            
            <div class="instructions">
                <h3>使用说明：</h3>
                <ul>
                    <li>支持批量上传多个PDF文件</li>
                    <li>选择标签位置（9个预设位置）</li>
                    <li>可自定义标签文本、字体、颜色和偏移</li>
                    <li>单个文件直接下载，多个文件打包ZIP下载</li>
                </ul>
            </div>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="pdfFile">选择PDF文件 (支持多选):</label>
                    <input type="file" id="pdfFile" name="pdfFile" accept=".pdf" multiple required>
                </div>
                
                <div class="form-group">
                    <label for="labelText">标签文本:</label>
                    <input type="text" id="labelText" name="labelText" value="Made in China">
                </div>
                
                <div class="form-group">
                    <label for="position">标签位置:</label>
                    <select id="position" name="position">
                        <option value="top-right">右上角</option>
                        <option value="top-left">左上角</option>
                        <option value="top-center">顶部居中</option>
                        <option value="middle-right">右侧中间</option>
                        <option value="middle-left">左侧中间</option>
                        <option value="middle-center">正中间</option>
                        <option value="bottom-right">右下角</option>
                        <option value="bottom-left">左下角</option>
                        <option value="bottom-center">底部居中</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="fontSize">字体大小:</label>
                    <input type="number" id="fontSize" name="fontSize" value="8" min="6" max="20">
                </div>
                
                <div class="form-group">
                    <label for="fontColor">字体颜色:</label>
                    <input type="color" id="fontColor" name="fontColor" value="#FF0000">
                </div>
                
                <div class="form-group">
                    <label for="xOffset">X轴偏移 (-50到50):</label>
                    <input type="number" id="xOffset" name="xOffset" value="0" min="-50" max="50">
                </div>
                
                <div class="form-group">
                    <label for="yOffset">Y轴偏移 (-50到50):</label>
                    <input type="number" id="yOffset" name="yOffset" value="0" min="-50" max="50">
                </div>
                
                <div class="form-group">
                    <label for="outputDir">输出目录 (服务器路径，留空则下载):</label>
                    <input type="text" id="outputDir" name="outputDir" placeholder="例如: /home/user/output 或留空下载">
                </div>
                
                <button type="submit">处理PDF</button>
            </form>
            
            <div id="result" class="result"></div>
        </div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('pdfFile');
                const files = fileInput.files;
                
                if (files.length === 0) {
                    alert('请选择至少一个PDF文件');
                    return;
                }
                
                const formData = new FormData();
                
                // 添加所有选中的文件
                for (let i = 0; i < files.length; i++) {
                    formData.append('pdfFile', files[i]);
                }
                
                // 添加其他参数
                formData.append('labelText', document.getElementById('labelText').value);
                formData.append('position', document.getElementById('position').value);
                formData.append('fontSize', document.getElementById('fontSize').value);
                formData.append('fontColor', document.getElementById('fontColor').value);
                formData.append('xOffset', document.getElementById('xOffset').value);
                formData.append('yOffset', document.getElementById('yOffset').value);
                formData.append('outputDir', document.getElementById('outputDir').value);
                
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `处理中，请稍候... (共${files.length}个文件)`;
                
                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const contentDisposition = response.headers.get('Content-Disposition');
                        
                        if (contentDisposition && contentDisposition.includes('attachment')) {
                            // 处理文件下载
                            const blob = await response.blob();
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            
                            if (contentDisposition.includes('processed_pdfs.zip')) {
                                a.href = url;
                                a.download = 'processed_pdfs.zip';
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                                resultDiv.innerHTML = `批量处理完成！${files.length}个文件已打包下载。`;
                            } else {
                                // 单个文件下载
                                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                                const filename = filenameMatch ? filenameMatch[1] : 'processed.pdf';
                                a.href = url;
                                a.download = filename;
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                                resultDiv.innerHTML = '处理完成！文件已下载。';
                            }
                            window.URL.revokeObjectURL(url);
                        } else {
                            // 显示文本结果
                            const text = await response.text();
                            resultDiv.innerHTML = text;
                        }
                    } else {
                        const error = await response.text();
                        resultDiv.innerHTML = '错误: ' + error;
                    }
                } catch (error) {
                    resultDiv.innerHTML = '错误: ' + error.message;
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/process', methods=['POST'])
def process_pdf():
    try:
        logger.info(f"收到处理请求，文件数量: {len(request.files.getlist('pdfFile'))}")
        
        if 'pdfFile' not in request.files:
            return '未选择文件', 400
        
        files = request.files.getlist('pdfFile')
        if not files or all(f.filename == '' for f in files):
            return '未选择文件', 400
        
        # 过滤出有效的文件
        valid_files = [f for f in files if f.filename != '']
        
        if not valid_files:
            return '未选择有效文件', 400
        
        logger.info(f"有效文件数量: {len(valid_files)}")
        
        # 获取表单参数
        label_text = request.form.get('labelText', 'Made in China')
        position = request.form.get('position', 'top-right')
        font_size = int(request.form.get('fontSize', 8))
        font_color = request.form.get('fontColor', '#FF0000')
        x_offset = int(request.form.get('xOffset', 0))
        y_offset = int(request.form.get('yOffset', 0))
        output_dir = request.form.get('outputDir', '').strip()
        
        logger.info(f"处理参数 - 位置: {position}, 文本: {label_text}, 字体大小: {font_size}")
        
        # 如果指定了输出目录，则处理所有文件并保存到该目录
        if output_dir:
            import os
            if not os.path.isdir(output_dir):
                return f"错误: 指定的目录不存在: {output_dir}", 400
            
            results = []
            for file in valid_files:
                if not allowed_file(file.filename):
                    results.append(f"跳过非PDF文件: {file.filename}")
                    continue
                
                try:
                    # 处理PDF
                    processed_pdf = add_label_to_pdf(
                        file.stream, 
                        position, 
                        x_offset, 
                        y_offset, 
                        font_size, 
                        font_color, 
                        label_text
                    )
                    
                    output_path = os.path.join(output_dir, f"processed_{secure_filename(file.filename)}")
                    with open(output_path, 'wb') as f:
                        f.write(processed_pdf.getvalue())
                    results.append(f"已保存: {output_path}")
                    logger.info(f"文件已保存至: {output_path}")
                except Exception as e:
                    error_msg = f"处理失败 {file.filename}: {str(e)}"
                    results.append(error_msg)
                    logger.error(error_msg)
            
            result_message = "\\n".join(results)
            return f"批量处理完成!\\n{result_message}"
        
        # 如果没有指定输出目录，则根据文件数量决定返回方式
        else:
            processed_files = []
            
            for file in valid_files:
                if not allowed_file(file.filename):
                    continue  # 跳过非PDF文件
                
                try:
                    # 处理PDF
                    processed_pdf = add_label_to_pdf(
                        file.stream, 
                        position, 
                        x_offset, 
                        y_offset, 
                        font_size, 
                        font_color, 
                        label_text
                    )
                    
                    processed_pdf.seek(0)
                    processed_files.append({
                        'original_filename': file.filename,
                        'data': processed_pdf.read()
                    })
                    logger.info(f"成功处理文件: {file.filename}")
                except Exception as e:
                    error_msg = f"处理失败 {file.filename}: {str(e)}"
                    logger.error(error_msg)
                    return error_msg, 500
            
            # 如果只有一个文件，直接返回该文件
            if len(processed_files) == 1:
                file_info = processed_files[0]
                filename = 'processed_' + secure_filename(file_info['original_filename'])
                file_data = file_info['data']
                
                from io import BytesIO
                file_io = BytesIO(file_data)
                file_io.seek(0)
                
                logger.info(f"返回单个文件: {filename}")
                return send_file(
                    file_io,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            
            # 如果有多个文件，打包成ZIP返回
            else:
                import zipfile
                from io import BytesIO
                
                # 创建内存中的ZIP文件
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_info in processed_files:
                        filename = 'processed_' + secure_filename(file_info['original_filename'])
                        zipf.writestr(filename, file_info['data'])
                
                zip_buffer.seek(0)
                
                logger.info(f"返回ZIP文件，包含 {len(processed_files)} 个文件")
                return send_file(
                    zip_buffer,
                    as_attachment=True,
                    download_name="processed_pdfs.zip",
                    mimetype='application/zip'
                )
        
    except Exception as e:
        error_msg = f"错误: {str(e)}"
        logger.error(error_msg)
        return error_msg, 500

if __name__ == '__main__':
    # 生产环境建议使用Gunicorn，此处仅为开发测试
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)