classdef NEMTParams
    %NEMTParams NEMT模型参数类
    %
    % 参数说明:
    %   alpha   - 扩散系数 (市场流动性指标)
    %   beta    - 非线性系数 (情绪/杠杆/羊群效应强度)
    %   noise   - 噪声水平 (外部扰动)
    %   dt      - 时间步长
    %   dx      - 空间步长
    %   steps   - 演化步数
    
    properties
        alpha (1,1) double = 0.1      % 扩散系数
        beta  (1,1) double = 1.0      % 非线性强度
        noise (1,1) double = 0.2      % 噪声水平
        dt    (1,1) double = 0.01     % 时间步长
        dx    (1,1) double = 1.0      % 空间步长
        steps (1,1) double = 200      % 演化步数
    end
    
    methods
        function obj = NEMTParams(alpha, beta, noise, dt, dx, steps)
            % 构造函数
            if nargin >= 1, obj.alpha = alpha; end
            if nargin >= 2, obj.beta = beta; end
            if nargin >= 3, obj.noise = noise; end
            if nargin >= 4, obj.dt = dt; end
            if nargin >= 5, obj.dx = dx; end
            if nargin >= 6, obj.steps = steps; end
        end
        
        function disp(obj)
            fprintf('NEMT参数:\n');
            fprintf('  alpha = %.4f (扩散系数)\n', obj.alpha);
            fprintf('  beta  = %.4f (非线性强度)\n', obj.beta);
            fprintf('  noise = %.4f (噪声水平)\n', obj.noise);
            fprintf('  dt    = %.4f (时间步长)\n', obj.dt);
            fprintf('  dx    = %.4f (空间步长)\n', obj.dx);
            fprintf('  steps = %d (演化步数)\n', obj.steps);
        end
    end
end
