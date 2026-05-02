# 标准化版单神经元.py
# 2026.4.23
# 作者：蜉蝣
# 编码：utf-8

import numpy as np

class Neuron:
    def __init__(self, input_size, activation='sigmoid'):
        """
        初始化单神经元
        :param input_size: 输入特征数量
        :param activation: 激活函数，支持 'sigmoid', 'relu', 'tanh'
        """
        # 初始化权重和偏置
        self.weights = np.random.randn(input_size) * 0.01
        self.bias = 0.0
        self.activation = activation
    
    def _sigmoid(self, x):
        """Sigmoid激活函数"""
        return 1 / (1 + np.exp(-x))
    
    def _sigmoid_derivative(self, x):
        """Sigmoid激活函数的导数"""
        return x * (1 - x)
    
    def _relu(self, x):
        """ReLU激活函数"""
        return np.maximum(0, x)
    
    def _relu_derivative(self, x):
        """ReLU激活函数的导数"""
        return np.where(x > 0, 1, 0)
    
    def _tanh(self, x):
        """Tanh激活函数"""
        return np.tanh(x)
    
    def _tanh_derivative(self, x):
        """Tanh激活函数的导数"""
        return 1 - np.tanh(x) ** 2
    
    def forward(self, X):
        """
        前向传播
        :param X: 输入数据，形状为 (batch_size, input_size)
        :return: 神经元输出
        """
        # 计算加权和
        self.z = np.dot(X, self.weights) + self.bias
        
        # 应用激活函数
        if self.activation == 'sigmoid':
            self.output = self._sigmoid(self.z)
        elif self.activation == 'relu':
            self.output = self._relu(self.z)
        elif self.activation == 'tanh':
            self.output = self._tanh(self.z)
        else:
            raise ValueError("不支持的激活函数")
        
        return self.output
    
    def backward(self, X, y, learning_rate=0.01):
        """
        反向传播
        :param X: 输入数据，形状为 (batch_size, input_size)
        :param y: 真实标签，形状为 (batch_size,)
        :param learning_rate: 学习率
        :return: 损失值
        """
        # 计算损失（均方误差）
        loss = np.mean((self.output - y) ** 2)
        
        # 计算梯度
        if self.activation == 'sigmoid':
            d_output = 2 * (self.output - y) * self._sigmoid_derivative(self.output)
        elif self.activation == 'relu':
            d_output = 2 * (self.output - y) * self._relu_derivative(self.z)
        elif self.activation == 'tanh':
            d_output = 2 * (self.output - y) * self._tanh_derivative(self.output)
        
        # 计算权重和偏置的梯度
        d_weights = np.dot(X.T, d_output) / X.shape[0]
        d_bias = np.mean(d_output)
        
        # 更新权重和偏置
        self.weights -= learning_rate * d_weights
        self.bias -= learning_rate * d_bias
        
        return loss
    
    def train(self, X, y, epochs=1000, learning_rate=0.01, verbose=False):
        """
        训练神经元
        :param X: 输入数据，形状为 (batch_size, input_size)
        :param y: 真实标签，形状为 (batch_size,)
        :param epochs: 训练轮数
        :param learning_rate: 学习率
        :param verbose: 是否打印训练过程
        """
        for epoch in range(epochs):
            # 前向传播
            self.forward(X)
            # 反向传播
            loss = self.backward(X, y, learning_rate)
            
            if verbose and (epoch + 1) % 100 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.4f}")
    
    def predict(self, X):
        """
        预测
        :param X: 输入数据，形状为 (batch_size, input_size)
        :return: 预测结果
        """
        return self.forward(X)

# 示例：使用单神经元解决线性可分的二分类问题
if __name__ == "__main__":
    # 生成训练数据（逻辑与问题，线性可分）
    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    y = np.array([0, 0, 0, 1])
    
    # 创建神经元实例
    neuron = Neuron(input_size=2, activation='sigmoid')
    
    # 训练神经元
    print("训练单神经元（逻辑与问题）...")
    neuron.train(X, y, epochs=5000, learning_rate=0.1, verbose=True)
    
    # 测试预测
    print("\n预测结果:")
    predictions = neuron.predict(X)
    for i in range(len(X)):
        print(f"输入: {X[i]}, 真实值: {y[i]}, 预测值: {predictions[i]:.4f}, 分类: {1 if predictions[i] > 0.5 else 0}")
    
    # 演示ReLU激活函数
    print("\n\n使用ReLU激活函数:")
    neuron_relu = Neuron(input_size=2, activation='relu')
    neuron_relu.train(X, y, epochs=5000, learning_rate=0.1, verbose=True)
    predictions_relu = neuron_relu.predict(X)
    print("\n预测结果:")
    for i in range(len(X)):
        print(f"输入: {X[i]}, 真实值: {y[i]}, 预测值: {predictions_relu[i]:.4f}, 分类: {1 if predictions_relu[i] > 0.5 else 0}")

