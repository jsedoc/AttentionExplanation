from Transparency.common_code.common import *
import sys
sys.path.append('preprocess/')
import vectorizer

def sortbylength(X, y) :
    len_t = np.argsort([len(x) for x in X])
    X1 = [X[i] for i in len_t]
    y1 = [y[i] for i in len_t]
    return X1, y1
    
def filterbylength(X, y, min_length = None, max_length = None) :
    lens = [len(x)-2 for x in X]
    min_l = min(lens) if min_length is None else min_length
    max_l = max(lens) if max_length is None else max_length

    idx = [i for i in range(len(X)) if len(X[i]) > min_l+2 and len(X[i]) < max_l+2]
    X = [X[i] for i in idx]
    y = [y[i] for i in idx]

    return X, y

def set_balanced_pos_weight(dataset) :
    y = np.array(dataset.train_data.y)
    dataset.pos_weight = [len(y) / sum(y) - 1]

class DataHolder() :
    def __init__(self, X, y) :
        self.X = X
        self.y = y
        self.attributes = ['X', 'y']

    def get_stats(self, field) :
        assert field in self.attributes
        lens = [len(x) - 2 for x in getattr(self, field)]
        return {
            'min_length' : min(lens),
            'max_length' : max(lens),
            'mean_length' : np.mean(lens),
            'std_length' : np.std(lens)
        }
    
    def mock(self, n=200) :
        data_kwargs = { key: getattr(self, key)[:n] for key in self.attributes}
        return DataHolder(**data_kwargs)

    def filter(self, idxs) :
        data_kwargs = { key: [getattr(self, key)[i] for i in idxs] for key in self.attributes}
        return DataHolder(**data_kwargs)

class Dataset() :
    def __init__(self, name, path=None, vec=None, min_length=None, max_length=None) :
        self.name = name
        self.vec = pickle.load(open(path, 'rb')) if vec is None else vec

        X, Xt = self.vec.seq_text['train'], self.vec.seq_text['test']
        y, yt = self.vec.label['train'], self.vec.label['test']

        X, y = filterbylength(X, y, min_length=min_length, max_length=max_length)
        Xt, yt = filterbylength(Xt, yt, min_length=min_length, max_length=max_length)
        Xt, yt = sortbylength(Xt, yt)

        self.train_data = DataHolder(X, y)
        self.test_data = DataHolder(Xt, yt)
        
        self.trainer_type = 'Single_Label'
        self.output_size = 1
        self.save_on_metric = 'roc_auc'
        self.keys_to_use = {
            'roc_auc' : 'roc_auc', 
            'pr_auc' : 'pr_auc'
        }

    def display_stats(self) :
        stats = {}
        stats['vocab_size'] = self.vec.vocab_size
        stats['embed_size'] = self.vec.word_dim
#         stats['hidden_size'] = self.vec.hidden_size
        y = np.unique(np.array(self.train_data.y), return_counts=True)
        yt = np.unique(np.array(self.test_data.y), return_counts=True)

        stats['train_size'] = list(zip(y[0].tolist(), y[1].tolist()))
        stats['test_size'] = list(zip(yt[0].tolist(), yt[1].tolist()))
        stats.update(self.train_data.get_stats('X'))

        outdir = "datastats"
        os.makedirs('graph_outputs/' + outdir, exist_ok=True)

        json.dump(stats, open('graph_outputs/' + outdir + '/' + self.name + '.txt', 'w'))
        print(stats)

########################################## Dataset Loaders ################################################################################

def SST_dataset() :
    dataset = Dataset(name='sst', path='preprocess/SST/sst.p', min_length=5)
    set_balanced_pos_weight(dataset)
    return dataset

def IMDB_dataset() :
    dataset = Dataset(name='imdb', path='preprocess/IMDB/imdb_data.p', min_length=6)
    set_balanced_pos_weight(dataset)
    return dataset

def News20_dataset() :
    dataset = Dataset(name='20News_sports', path='preprocess/20News/vec_sports.p', min_length=6, max_length=500)
    set_balanced_pos_weight(dataset)
    return dataset

def ADR_dataset() :
    dataset = Dataset(name='tweet', path='preprocess/Tweets/vec_adr.p', min_length=5, max_length=100)
    set_balanced_pos_weight(dataset)
    return dataset

def Anemia_dataset() :
    dataset = Dataset(name='anemia', path='preprocess/MIMIC/vec_icd9_anemia.p', max_length=4000)
    set_balanced_pos_weight(dataset)
    return dataset

def generate_diabetes() :
    vec = pickle.load(open('preprocess/MIMIC/vec_icd9.p', 'rb'))
    diabetes_label = vec.label2idx['250.00']
    X, Xt = vec.seqs['train'], vec.seqs['test']
    y, yt = vec.label_one_hot['train'][:, diabetes_label], vec.label_one_hot['test'][:, diabetes_label]

    vec.seq_text = {'train' : X, 'test' : Xt}
    vec.label = {'train' : y, 'test' : yt}

    vec.seqs = None
    vec.label_one_hot = None

    return Dataset(name='diab', path=None, vec=vec, min_length=6, max_length=4000)

def Diabetes_dataset() :
    dataset = generate_diabetes()
    set_balanced_pos_weight(dataset)
    return dataset

def AGNews_dataset() :
    dataset = Dataset(name='agnews', path='preprocess/ag_news/vec.p')
    set_balanced_pos_weight(dataset)
    return dataset

datasets = {
    "sst" : SST_dataset,
    "imdb" : IMDB_dataset,
    "20News_sports" : News20_dataset,
    "tweet" : ADR_dataset ,
    "Anemia" : Anemia_dataset,
    "Diabetes" : Diabetes_dataset,
    "AgNews" : AGNews_dataset
}

####################################### EHR Dataloaders ######################################################################

def Readmission_dataset() :
    dataset = Dataset(name='readmission', path='preprocess/MIMIC_Datasets/Readmission/readmission.p', max_length=20000)
    set_balanced_pos_weight(dataset)
    dataset.test_data = dataset.test_data.mock(n=5000)
    return dataset

def Mortality_dataset() :
    dataset = Dataset(name='mortality', path='preprocess/MIMIC_Datasets/Mortality/mortality.p', max_length=20000)
    set_balanced_pos_weight(dataset)
    dataset.test_data = dataset.test_data.mock(n=5000)
    return dataset

def KneeSurgery_dataset() :
    dataset = Dataset(name='KneeSurgery', path='preprocess/MIMIC_Datasets/KneeSurgery/kneesurgery.p', max_length=20000)
    set_balanced_pos_weight(dataset)
    dataset.test_data = dataset.test_data.mock(n=5000)
    return dataset

def HipSurgery_dataset() :
    dataset = Dataset(name='HipSurgery', path='preprocess/MIMIC_Datasets/HipSurgery/hipsurgery.p', max_length=20000)
    set_balanced_pos_weight(dataset)
    dataset.test_data = dataset.test_data.mock(n=5000)
    return dataset

def Phenotyping_dataset() :
    dataset = Dataset(name='Phenotyping', path='preprocess/MIMIC_Datasets/Diagnosis/diagnosis.p', max_length=20000)
    y = np.array(dataset.train_data.y)
    dataset.pos_weight = list(len(y) / y.sum(0) - 1)
    
    dataset.trainer_type = 'Multi_Label'
    dataset.save_on_metric = 'macro_roc_auc'
    dataset.output_size = len(dataset.pos_weight)
    dataset.test_data = dataset.test_data.mock(n=5000)

    dataset.keys_to_use = {
        'macro_roc_auc' : 'roc_auc', 
        'macro_pr_auc' : 'pr_auc'
    }
    return dataset

datasets_ehr = {
    "readmission" : Readmission_dataset,
    "mortality" : Mortality_dataset,
    'knee' : KneeSurgery_dataset,
    'hip' : HipSurgery_dataset,
    'pheno' : Phenotyping_dataset
}
