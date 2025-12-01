const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const WebSocket = require('ws');
const http = require('http');
const os = require('os');

const app = express();

// 获取本机IP地址
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      // 跳过内部和非IPv4地址
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return 'localhost';
}

const serverIP = getLocalIP();
const PORT = process.env.PORT || 3000;

const DATA_FILE = path.join(__dirname, 'data.json');

// 创建HTTP服务器
const server = http.createServer(app);

// 创建WebSocket服务器
const wss = new WebSocket.Server({ server });

// 存储连接的客户端
const clients = {
  web: null,
  app: null
};

// 中间件
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

// 初始化数据文件
const initDataFile = () => {
  if (!fs.existsSync(DATA_FILE)) {
    const initialData = {
      currentParams: {
        input: '',
        output: ''
      },
      history: []
    };
    fs.writeFileSync(DATA_FILE, JSON.stringify(initialData, null, 2));
  }
};

// 读取数据
const readData = () => {
  try {
    const data = fs.readFileSync(DATA_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error reading data:', error);
    return { currentParams: { input: '', output: '' }, history: [] };
  }
};

// 写入数据
const writeData = (data) => {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
    return true;
  } catch (error) {
    console.error('Error writing data:', error);
    return false;
  }
};

// API路由

// 获取当前参数（供App端调用）
app.get('/api/current-params', (req, res) => {
  const data = readData();
  res.json(data.currentParams);
});

// 设置当前参数
app.post('/api/current-params', (req, res) => {
  const { input, output } = req.body;
  const data = readData();
  
  data.currentParams = {
    input: input || '',
    output: output || ''
  };
  
  if (writeData(data)) {
    res.json({ success: true, data: data.currentParams });
  } else {
    res.status(500).json({ success: false, message: '保存失败' });
  }
});

// 获取所有历史记录
app.get('/api/history', (req, res) => {
  const data = readData();
  res.json(data.history);
});

// 保存到历史记录（以function为主键）
app.post('/api/history', (req, res) => {
  const { input, output } = req.body;
  const data = readData();
  
  // 尝试从input中提取function
  let functionName = '未知函数';
  try {
    const inputObj = typeof input === 'string' ? JSON.parse(input) : input;
    functionName = inputObj.function || '未知函数';
  } catch (error) {
    console.log('解析input失败，使用默认function名称');
  }
  
  // 查找是否已存在该function的记录
  const existingIndex = data.history.findIndex(item => item.function === functionName);
  
  if (existingIndex !== -1) {
    // 已存在，更新记录
    data.history[existingIndex] = {
      ...data.history[existingIndex],
      input: input || '',
      output: output || '',
      timestamp: new Date().toISOString()
    };
    
    if (writeData(data)) {
      res.json({ success: true, data: data.history[existingIndex], updated: true });
    } else {
      res.status(500).json({ success: false, message: '更新失败' });
    }
  } else {
    // 不存在，新增记录
    const newRecord = {
      id: Date.now(),
      function: functionName,
      input: input || '',
      output: output || '',
      timestamp: new Date().toISOString()
    };
    
    data.history.unshift(newRecord);
    
    // 限制历史记录数量为50条
    if (data.history.length > 50) {
      data.history = data.history.slice(0, 50);
    }
    
    if (writeData(data)) {
      res.json({ success: true, data: newRecord, updated: false });
    } else {
      res.status(500).json({ success: false, message: '保存失败' });
    }
  }
});

// 更新历史记录
app.put('/api/history/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const { input, output, name } = req.body;
  const data = readData();
  
  const index = data.history.findIndex(item => item.id === id);
  if (index !== -1) {
    data.history[index] = {
      ...data.history[index],
      input: input !== undefined ? input : data.history[index].input,
      output: output !== undefined ? output : data.history[index].output,
      name: name !== undefined ? name : data.history[index].name,
    };
    
    if (writeData(data)) {
      res.json({ success: true, data: data.history[index] });
    } else {
      res.status(500).json({ success: false, message: '更新失败' });
    }
  } else {
    res.status(404).json({ success: false, message: '记录不存在' });
  }
});

// 删除历史记录
app.delete('/api/history/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const data = readData();
  
  const index = data.history.findIndex(item => item.id === id);
  if (index !== -1) {
    data.history.splice(index, 1);
    
    if (writeData(data)) {
      res.json({ success: true });
    } else {
      res.status(500).json({ success: false, message: '删除失败' });
    }
  } else {
    res.status(404).json({ success: false, message: '记录不存在' });
  }
});

// 获取所有测试数据
app.get('/api/test/run-all', (req, res) => {
  try {
    const testDataDir = path.join(__dirname, '../../FuncApp4NAL2/input_json_data');
    const files = fs.readdirSync(testDataDir).filter(f => f.endsWith('.json')).sort();
    
    const allTests = files.map(file => {
      const filePath = path.join(testDataDir, file);
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    });
    
    res.json(allTests);
  } catch (error) {
    console.error('读取测试数据失败:', error);
    res.status(500).json({ error: error.message });
  }
});

// 处理NAL2函数调用（通过WebSocket转发到App）
app.post('/api/nal2/process', async (req, res) => {
  try {
    const input = req.body;
    
    // 检查App是否连接
    if (!clients.app || clients.app.readyState !== WebSocket.OPEN) {
      return res.status(503).json({
        sequence_num: input.sequence_num || 0,
        function: input.function || 'unknown',
        return: -1,
        output_parameters: {
          error: 'App未连接或已断开'
        }
      });
    }
    
    // 创建Promise等待App响应
    const response = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('请求超时'));
      }, 30000); // 30秒超时
      
      // 设置临时消息处理器
      const messageHandler = (message) => {
        try {
          const data = JSON.parse(message);
          if (data.type === 'nal2_response' && data.sequence_num === input.sequence_num) {
            clearTimeout(timeout);
            clients.app.removeListener('message', messageHandler);
            resolve(data.result);
          }
        } catch (error) {
          // 忽略解析错误
        }
      };
      
      clients.app.on('message', messageHandler);
      
      // 发送请求到App
      clients.app.send(JSON.stringify({
        type: 'nal2_request',
        data: input
      }));
    });
    
    res.json(response);
    
  } catch (error) {
    console.error('处理NAL2请求失败:', error);
    res.status(500).json({
      sequence_num: req.body.sequence_num || 0,
      function: req.body.function || 'unknown',
      return: -1,
      output_parameters: {
        error: error.message
      }
    });
  }
});

// 根路径
app.get('/', (req, res) => {
  res.send(`
    <html>
      <head><title>NAL2 Server</title></head>
      <body>
        <h1>NAL2 参数管理服务器</h1>
        <p>服务器运行中...</p>
        <p>API端点:</p>
        <ul>
          <li>GET /api/current-params - 获取当前参数</li>
          <li>POST /api/current-params - 设置当前参数</li>
          <li>GET /api/history - 获取历史记录</li>
          <li>POST /api/history - 保存历史记录</li>
          <li>POST /api/nal2/process - 处理NAL2函数调用</li>
        </ul>
      </body>
    </html>
  `);
});

// WebSocket连接处理
wss.on('connection', (ws, req) => {
  console.log('新的WebSocket连接');
  
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      console.log('收到消息:', data);
      
      // 根据类型注册客户端
      if (data.type === 'register') {
        if (data.client === 'web') {
          clients.web = ws;
          console.log('Web客户端已连接');
          ws.send(JSON.stringify({ type: 'registered', client: 'web' }));
        } else if (data.client === 'app') {
          clients.app = ws;
          console.log('App客户端已连接');
          ws.send(JSON.stringify({ type: 'registered', client: 'app' }));
        }
      }
      
      // Web端发送input给App处理
      else if (data.type === 'send_to_app') {
        console.log('Web端发送input给App:', data.input);
        if (clients.app && clients.app.readyState === WebSocket.OPEN) {
          clients.app.send(JSON.stringify({
            type: 'process_input',
            input: data.input
          }));
        } else {
          // App未连接，通知Web端
          if (clients.web && clients.web.readyState === WebSocket.OPEN) {
            clients.web.send(JSON.stringify({
              type: 'error',
              message: 'App未连接'
            }));
          }
        }
      }
      
      // App处理完成，发送output给Web
      else if (data.type === 'send_to_web') {
        console.log('App发送output给Web:', data.output);
        if (clients.web && clients.web.readyState === WebSocket.OPEN) {
          clients.web.send(JSON.stringify({
            type: 'receive_output',
            output: data.output
          }));
        }
      }
      
    } catch (error) {
      console.error('处理WebSocket消息错误:', error);
    }
  });
  
  ws.on('close', () => {
    console.log('WebSocket连接关闭');
    // 清理断开的客户端
    if (clients.web === ws) {
      clients.web = null;
      console.log('Web客户端已断开');
    }
    if (clients.app === ws) {
      clients.app = null;
      console.log('App客户端已断开');
    }
  });
  
  ws.on('error', (error) => {
    console.error('WebSocket错误:', error);
  });
});

// 启动服务器
initDataFile();

server.listen(PORT, '0.0.0.0', () => {
  console.log('\n========================================');
  console.log('NAL2 参数管理服务器已启动');
  console.log('========================================');
  console.log(`本地访问: http://localhost:${PORT}`);
  console.log(`局域网访问: http://${serverIP}:${PORT}`);
  console.log(`WebSocket: ws://${serverIP}:${PORT}`);
  console.log('========================================\n');
});
