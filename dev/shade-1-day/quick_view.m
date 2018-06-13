% generate scaled single-band images from hourly insolation tifs

% tif_files = dir('*_*h.tif');
% for ii = 1:length(tif_files)
%     disp(tif_files(ii).name);
%     tif = imread(tif_files(ii).name);
%     if ii == 1
%         shade = nan(size(tif, 1), size(tif, 2), length(tif_files));
%     end
%     shade(:, :, ii) = tif(:,:,4); % idw band
% end
% shade(shade==-9999) = NaN;

min_shade = min(shade(:));
max_shade = max(shade(:));
for ii = 1:size(shade, 3)
    imagesc(shade(:,:,ii));
    caxis([min_shade, max_shade]);
    colormap(gray);
    colorbar;
    title(ii);
    pause
end
