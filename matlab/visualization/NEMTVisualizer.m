classdef NEMTVisualizer
    %NEMTVisualizer NEMT可视化工具箱
    
    methods (Static)
        function h = plotSpectrum(freqs, spectrum, varargin)
            % plotSpectrum 绘制频谱图
            %
            % 输入:
            %   freqs   - 频率轴
            %   spectrum - 频谱振幅
            %   varargin - 可选参数: 'Title', 'SavePath'
            
            p = inputParser;
            addOptional(p, 'Title', '频谱结构', @ischar);
            addOptional(p, 'SavePath', '', @ischar);
            parse(p, varargin{:});
            
            h = figure('Units', 'normalized', 'Position', [0.1, 0.1, 0.8, 0.5]);
            
            plot(freqs, spectrum, 'b-', 'LineWidth', 1.5);
            hold on;
            fill(freqs, spectrum, 'b', 'FaceAlpha', 0.3);
            
            % 标记峰值
            power = spectrum.^2;
            threshold = mean(power) * 2;
            peaksIdx = find(power > threshold);
            if ~isempty(peaksIdx)
                scatter(freqs(peaksIdx), spectrum(peaksIdx), 50, 'r', 'filled');
            end
            
            xlabel('频率', 'FontSize', 12);
            ylabel('振幅', 'FontSize', 12);
            title(p.Results.Title, 'FontSize', 14, 'FontWeight', 'bold');
            grid on;
            legend('频谱振幅', '共振峰', 'Location', 'best');
            
            if ~isempty(p.Results.SavePath)
                saveas(h, p.Results.SavePath);
            end
        end
        
        function h = plotEvolution(evolution, dt, varargin)
            % plotEvolution 绘制时空演化图
            %
            % 输入:
            %   evolution - 演化矩阵 (N x steps)
            %   dt        - 时间步长
            
            p = inputParser;
            addOptional(p, 'Title', '市场波动演化', 'FontSize', 12);
            addOptional(p, 'SavePath', '', @ischar);
            parse(p, varargin{:});
            
            h = figure('Units', 'normalized', 'Position', [0.1, 0.1, 0.8, 0.6]);
            
            [N, steps] = size(evolution);
            extent = [0, steps*dt, 0, N];
            
            imagesc(extent, 1:N, evolution);
            colorbar;
            colormap('viridis');
            
            xlabel('时间 (t)', 'FontSize', 12);
            ylabel('空间索引', 'FontSize', 12);
            title(p.Results.Title, 'FontSize', 14, 'FontWeight', 'bold');
            
            if ~isempty(p.Results.SavePath)
                saveas(h, p.Results.SavePath);
            end
        end
        
        function h = plotNoiseExperiment(results, noiseLevels, varargin)
            % plotNoiseExperiment 绘制噪声扫描实验结果
            %
            % 输入:
            %   results     - 实验结果结构体数组
            %   noiseLevels - 噪声水平列表

            p = inputParser;
            addOptional(p, 'SavePath', '', @ischar);
            parse(p, varargin{:});

            h = figure('Units', 'normalized', 'Position', [0.05, 0.05, 0.9, 0.85], ...
                'Name', '噪声扫描实验', 'NumberTitle', 'off', 'Visible', 'on');

            % 创建子图布局
            subplot(2, 2, 1);
            spectralWidths = [results.spectralWidth];
            plot(noiseLevels, spectralWidths, 'bo-', 'LineWidth', 2, 'MarkerSize', 8);
            xlabel('噪声水平 \eta', 'FontSize', 11);
            ylabel('谱宽', 'FontSize', 11);
            title('谱宽随噪声变化', 'FontSize', 12, 'FontWeight', 'bold');
            grid on;

            % 频谱叠加
            subplot(2, 2, 2);
            colors = lines(length(noiseLevels));
            for i = 1:min(length(results), 6)
                plot(results(i).freqs, results(i).spectrum, ...
                    'Color', colors(i,:), 'LineWidth', 1.2);
                hold on;
            end
            xlabel('频率', 'FontSize', 11);
            ylabel('振幅', 'FontSize', 11);
            title('不同噪声水平下的频谱', 'FontSize', 12, 'FontWeight', 'bold');
            legend(arrayfun(@(x) sprintf('\\eta=%.2f', x), noiseLevels, 'UniformOutput', false));
            grid on;

            % 演化图1
            if length(results) >= 1 && isfield(results(1), 'evolution') && ~isempty(results(1).evolution)
                subplot(2, 2, 3);
                imagesc(results(1).evolution);
                colormap('plasma');
                colorbar;
                title(sprintf('演化图 \\eta=%.2f', noiseLevels(1)), 'FontSize', 11);
            else
                subplot(2, 2, 3);
                text(0.5, 0.5, '演化数据不可用', 'HorizontalAlignment', 'center', 'FontSize', 12);
                title('演化图', 'FontSize', 11);
            end

            % 演化图2
            if length(results) >= 2 && isfield(results(2), 'evolution') && ~isempty(results(2).evolution)
                subplot(2, 2, 4);
                imagesc(results(2).evolution);
                colormap('plasma');
                colorbar;
                title(sprintf('演化图 \\eta=%.2f', noiseLevels(2)), 'FontSize', 11);
            else
                subplot(2, 2, 4);
                text(0.5, 0.5, '演化数据不可用', 'HorizontalAlignment', 'center', 'FontSize', 12);
                title('演化图', 'FontSize', 11);
            end

            sgtitle('噪声扫描实验', 'FontSize', 16, 'FontWeight', 'bold');

            % 强制显示图形
            drawnow;
            set(h, 'Visible', 'on');

            if ~isempty(p.Results.SavePath)
                saveas(h, p.Results.SavePath);
            end
        end
        
        function h = plotNonlinearExperiment(results, betaValues, varargin)
            % plotNonlinearExperiment 绘制非线性扫描实验结果

            p = inputParser;
            addOptional(p, 'SavePath', '', @ischar);
            parse(p, varargin{:});

            h = figure('Units', 'normalized', 'Position', [0.05, 0.05, 0.9, 0.85], ...
                'Name', '非线性扫描实验', 'NumberTitle', 'off', 'Visible', 'on');

            % 谱宽 vs β
            subplot(2, 2, 1);
            spectralWidths = [results.spectralWidth];
            plot(betaValues, spectralWidths, 'ro-', 'LineWidth', 2, 'MarkerSize', 8);
            xlabel('\beta (非线性强度)', 'FontSize', 11);
            ylabel('谱宽', 'FontSize', 11);
            title('谱宽随非线性强度变化', 'FontSize', 12, 'FontWeight', 'bold');
            grid on;

            % 频谱对比
            subplot(2, 2, 2);
            colors = lines(length(betaValues));
            for i = 1:min(length(results), 6)
                plot(results(i).freqs, results(i).spectrum, ...
                    'Color', colors(i,:), 'LineWidth', 1.2);
                hold on;
            end
            xlabel('频率', 'FontSize', 11);
            ylabel('振幅', 'FontSize', 11);
            title('不同非线性强度下的频谱', 'FontSize', 12, 'FontWeight', 'bold');
            legend(arrayfun(@(x) sprintf('\\beta=%.2f', x), betaValues, 'UniformOutput', false));
            grid on;

            % 振幅分布
            subplot(2, 2, 3);
            for i = 1:min(length(results), 3)
                histogram(abs(results(i).psi), 30, 'FaceAlpha', 0.5);
                hold on;
            end
            xlabel('|\psi|', 'FontSize', 11);
            ylabel('频数', 'FontSize', 11);
            title('振幅分布', 'FontSize', 12, 'FontWeight', 'bold');
            legend(arrayfun(@(x) sprintf('\\beta=%.2f', x), betaValues(1:3), 'UniformOutput', false));
            grid on;

            % 演化图
            if length(results) >= 1 && isfield(results(end), 'evolution') && ~isempty(results(end).evolution)
                subplot(2, 2, 4);
                imagesc(results(end).evolution);
                colormap('magma');
                colorbar;
                title(sprintf('演化图 \\beta=%.2f', betaValues(end)), 'FontSize', 11);
            else
                subplot(2, 2, 4);
                text(0.5, 0.5, '演化数据不可用', 'HorizontalAlignment', 'center', 'FontSize', 12);
                title('演化图', 'FontSize', 11);
            end

            sgtitle('非线性扫描实验', 'FontSize', 16, 'FontWeight', 'bold');

            % 强制显示图形
            drawnow;
            set(h, 'Visible', 'on');

            if ~isempty(p.Results.SavePath)
                saveas(h, p.Results.SavePath);
            end
        end
        
        function h = plotResonanceAnalysis(psi, spectrum, freqs, resonance, varargin)
            % plotResonanceAnalysis 绘制共振分析图
            
            p = inputParser;
            addOptional(p, 'SavePath', '', @ischar);
            parse(p, varargin{:});
            
            h = figure('Units', 'normalized', 'Position', [0.1, 0.1, 0.8, 0.8]);
            
            % 振幅时间序列
            subplot(2, 2, 1);
            plot(abs(psi), 'g-', 'LineWidth', 0.8);
            xlabel('索引', 'FontSize', 11);
            ylabel('|\psi|', 'FontSize', 11);
            title('|\psi(t)| 振幅演化', 'FontSize', 12, 'FontWeight', 'bold');
            grid on;
            
            % 相位
            subplot(2, 2, 2);
            plot(angle(psi), 'Color', [0.5, 0, 0.5], 'LineWidth', 0.5);
            xlabel('索引', 'FontSize', 11);
            ylabel('相位 (rad)', 'FontSize', 11);
            title('相位 arg(\psi)', 'FontSize', 12, 'FontWeight', 'bold');
            grid on;
            
            % 频谱与共振峰
            subplot(2, 2, 3);
            plot(freqs, spectrum, 'b-', 'LineWidth', 1.2);
            hold on;
            if resonance.numPeaks > 0
                scatter(resonance.peakFrequencies, resonance.peakAmplitudes, ...
                    100, 'r', 'filled', 'v');
            end
            xlabel('频率', 'FontSize', 11);
            ylabel('振幅', 'FontSize', 11);
            title(sprintf('频谱与共振峰 (%d个)', resonance.numPeaks), 'FontSize', 12, 'FontWeight', 'bold');
            legend('频谱', '共振峰', 'Location', 'best');
            grid on;
            
            % 功率谱
            subplot(2, 2, 4);
            power = spectrum.^2;
            semilogy(freqs, power, 'r-', 'LineWidth', 1.2);
            xlabel('频率', 'FontSize', 11);
            ylabel('功率', 'FontSize', 11);
            title('功率谱 (对数坐标)', 'FontSize', 12, 'FontWeight', 'bold');
            grid on;
            
            sgtitle('共振分析', 'FontSize', 16, 'FontWeight', 'bold');
            
            if ~isempty(p.Results.SavePath)
                saveas(h, p.Results.SavePath);
            end
        end
    end
end
