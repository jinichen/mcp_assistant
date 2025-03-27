import React from 'react';
import '../styles/chat.css';
import { Send } from 'lucide-react';

export function TestStyles() {
  return (
    <div className="chat-container">
      <h2>聊天界面演示</h2>
      
      <div className="message-container">
        <div className="chat-message assistant-message">
          <div className="message-bubble assistant-bubble">
            <div className="message-content">
              <p>👋 欢迎使用ASA智能助手! 我可以帮助您回答问题、提供信息，或协助处理各种任务。</p>
              <p>您可以询问我任何问题，或者上传图片进行分析。</p>
            </div>
          </div>
        </div>
        
        <div className="chat-message user-message">
          <div className="message-bubble user-bubble">
            <div className="message-content">
              <p>你能推荐一些适合周末游览的景点吗？最好是适合全家出游的。</p>
            </div>
          </div>
        </div>
        
        <div className="chat-message assistant-message">
          <div className="message-bubble assistant-bubble">
            <div className="message-content">
              <p>当然可以！这里有几个适合全家周末游览的景点推荐：</p>
              <ol>
                <li><strong>城市公园</strong> - 大多数公园有儿童游乐设施、步行道和野餐区，非常适合全家人。</li>
                <li><strong>自然保护区</strong> - 提供轻松徒步和自然观察的机会，让孩子们接触大自然。</li>
                <li><strong>互动博物馆</strong> - 特别是科学或儿童博物馆，通常有适合各年龄段的展览。</li>
                <li><strong>农场或果园</strong> - 如果季节合适，采摘水果或参观农场动物是很棒的家庭活动。</li>
              </ol>
              <p>您有特别偏好的活动类型或距离限制吗？我可以根据这些信息提供更具体的建议。</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="input-container">
        <input type="text" className="chat-input" placeholder="输入您的消息..." />
        <button className="send-button">
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}

export default TestStyles; 