import functools

def lazyprop(fn):
    attr_name = '_lazy_' + fn.__name__

    @property
    @functools.wraps(fn)
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazyprop

class DataSet:

    def __init__(self, path, repo='pcm-dpc/COVID-19', date_cols=['data'], index_cols=['data'], resample=False):
        self.repo = repo
        self.path = path
        self.commit_url = f'https://api.github.com/repos/{self.repo}/commits?path={self.path}&page=1&per_page=1'
        self.data_url = f'https://raw.githubusercontent.com/{self.repo}/master/{self.path}'
        self.resample = resample
        self.date_cols = date_cols
        self.index_cols = index_cols
    
    @lazyprop
    def last_modified(self):
        with urllib.request.urlopen(self.commit_url) as url:
            data = json.loads(url.read().decode())
            date = data[0]['commit']['committer']['date']
            utc_date = dateutil.parser.parse(date)
            return utc_date.astimezone(dateutil.tz.gettz('Italy/Rome'))

    @lazyprop
    def df(self):
        df = pd.read_csv(self.data_url, parse_dates=self.date_cols, index_col=self.index_cols)
        if self.resample:
            df = df.resample('D').last()
        return df
        
    def __repr__(self):
        return (f'DataSet\n  repo: {self.repo}\n  path: {self.path}\n  commit_url: {self.commit_url}\n'
                f'  last_modified: {self.last_modified}\n  data_url: {self.data_url}\n  df: {len(self.df)} items')
