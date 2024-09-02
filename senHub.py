from sentinelhub import (
    MimeType,
    CRS,
    BBox,
    SentinelHubRequest,
    DataCollection,
    bbox_to_dimensions,
)
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

class SenHub:
    ''' 
    Class For handling requests to Senhub API.
    '''
    def __init__(self,config,  resolution = 10,
                data_source = DataCollection.SENTINEL2_L1C,
                identifier ='default', mime_type = MimeType.TIFF):
        self.resolution = resolution
        self.config = config
        self.setInputParameters(data_source)
        self.setOutputParameters(identifier, mime_type)
        self.set_token()

    def setInputParameters(self, data_source):
        '''
        Select Source Satellite 
        '''
        self.data_source = data_source
    
    def setOutputParameters(self,identifier, mime_type):
        '''
        Select The return Type of request format and identifier
        '''
        self.identifier = identifier
        self.mime_type = mime_type

    def set_token(self):
        '''
        Fetch Tooken from sentinelhub api to be used for available dates 
        '''
        client_id = self.config.sh_client_id
        client_secret = self.config.sh_client_secret
        client = BackendApplicationClient(client_id=client_id)
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token(token_url='https://services.sentinel-hub.com/oauth/token',client_secret=client_secret)
        self.token =  token['access_token']

    def get_input_data(self, date):
        '''
        Wrap input_data to provide to the sentinelhub API
        '''
        return SentinelHubRequest.input_data(data_collection=self.data_source, time_interval=(date, date))

    def get_output_data(self):
        '''
        Wrap output_data to provide to the sentinelhub API
        '''
        return SentinelHubRequest.output_response(self.identifier, self.mime_type)
        
    def set_dir(self, dir_path):
        '''
        Set The Tragt Download Directory Path
        '''
        self.dir_path = dir_path

    def make_bbox(self, bbox):
        '''
        Wrap bbox to provide to the sentinelhub API.
        '''
        self.bbox = BBox(bbox=bbox, crs=CRS.WGS84)
        self.bbox_size = bbox_to_dimensions(self.bbox, resolution=self.resolution)
                
    def make_request(self, metric, date):
        '''
        Setup the Sentinal Hub Request
        '''
        input_data = self.get_input_data(date)
        output_data = self.get_output_data()
        self.request = SentinelHubRequest(
            data_folder=self.dir_path,
            evalscript=metric,
            input_data=[input_data],
            responses=[output_data],
            bbox=self.bbox,
            size=self.bbox_size,
            config=self.config,
            )

    def download_data(self, save=True , redownload=False):
        '''
        Make The Request and download the data
        '''
        return self.request.get_data(save_data=save, redownload=redownload)




