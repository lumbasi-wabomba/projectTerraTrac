import ee
ee.Initialize(project='terratrac')

def __init__(self, lat, long, buffer_size=250):
    self.point = ee.geometry.Point(long, lat)
    self.buffer = self.point.buffer(buffer_size)

def mask_cloud(self,img):
    qa = img.select('QA60')
    cloud_mask = qa.bitwiseAnd(1 << 10).eq(0).And( qa.bitwiseAnd(1 << 11).eq(0))
    return img.updateMask(cloud_mask).divide(10000)

def composite(self, start, end):
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
               .filterBounds(self.buffer)
               .filterDate(start, end)
               .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
               .map(self.mask_cloud))
    return col.median()

def ndvi(self, img):
    ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return ndvi

def mean_ndvi(self, start, end):
    img = self.composite(start, end)
    ndvi_img = self.ndvi(img)
    mean_dict = ndvi_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=self.buffer, scale=10)
    mean_ndvi = mean_dict.get('NDVI').getInfo()
    return mean_ndvi

def compare_ndvi(self, start1, end1, start2, end2):
    mean_ndvi1 = self.mean_ndvi(start1, end1)
    mean_ndvi2 = self.mean_ndvi(start2, end2)
    return mean_ndvi1, mean_ndvi2

def change_detection(self, start1, end1, start2, end2):
    mean_ndvi1 = self.mean_ndvi(start1, end1)
    mean_ndvi2 = self.mean_ndvi(start2, end2)
    change = mean_ndvi2 - mean_ndvi1

    if change < 0:
        return 'Deforestation', change
    elif change > 0:
        return 'Afforestation', change
    else:
        return 'No Change', change
