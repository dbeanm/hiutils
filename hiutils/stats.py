import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind
from statsmodels.stats.multitest import multipletests
from math import log10, floor
import numpy as np
import statsmodels.api as sm

#with some combinations of packages this is needed to get summary working again for Logit
# from scipy import stats
# stats.chisqprob = lambda chisq, df: stats.chi2.sf(chisq, df)

#### TODO
# summarise()
# 1. is the f parameter needed? or should it be changed to n_pct and set which variables become N (%)?
# f should default to all column names
# 2. add handling of groups with more than 2 values i.e. a vs b vs c?
# 3. add conveting a string group to booleans?
# new functions
# add handling of table multilevel index template

def summarise(data, f, med_iqr = [], mean_sd = []):
    """Generate summary stats
    med_iqr factors will be calculated as median (IQR), 
    mean_sd will be mean (sd)
    others n (%)
    Note - this does not check whether the test is appropriate to your data. 

    Parameters
    ----------

    Returns
    _______

    """
    
    data_n = data[f].sum().astype(int)
    data_p = (data_n / data.shape[0]) * 100
    data_p = data_p.round(1)
    
    o_v = data_n.astype(str) + " (" + data_p.astype(str) + "%)"
    
    for x in mean_sd:
        ov_age_m = data[x].mean()
        ov_age_sd = data[x].std()
        # ov_age_m + " (" + ov_age_sd + ")"
        o_v[x] = "{:0.2f} ({:0.2f})".format(ov_age_m, ov_age_sd)
    
    for x in med_iqr:
        Q1 = data[x].quantile(0.25)
        Q3 = data[x].quantile(0.75)
        IQR = Q3 - Q1
        ov_age_m = data[x].median() #.round(2).astype(str)
        #o_v[x] = ov_age_m + " (" + IQR + ")"
        o_v[x] = "{:0.2f} ({:0.2f})".format(ov_age_m, IQR)
        
    o_v['N'] = str(data.shape[0])
    
    #ov_name = "Overall (N=" + str(overall.shape[0]) + ")"
    #tbl = pd.DataFrame({ov_name: o_v})
    return o_v

def summarise_data(data, cols, rows, med_iqr = [], mean_sd = [], with_not = True, 
                   overall="Overall", tests = None, correct=True):
    """
    
    Parameters
    ----------

    overall : str or None
        Set the column name for the overall (all rows) stats
        If None the overall column is disabled

    Returns
    _______

    """

    tbl = pd.DataFrame()
    if overall != None:
        tbl[overall] = summarise(data, rows, med_iqr, mean_sd)
    for d in cols:
        on = data[data[d]]
        not_on = data[~data[d]]
        s_on = summarise(on, rows, med_iqr, mean_sd)
        s_not_on = summarise(not_on, rows, med_iqr, mean_sd)
        tbl[d] = s_on
        if with_not:
            tbl['Not ' + d] = s_not_on
        #stats
        if tests != None:
            pvals = []
            raw_name = 'Raw p-value ' + d + ' vs. Not ' + d
            corr_name = 'Corrected p-value ' + d + ' vs. Not ' + d
            for index, row in tbl.iterrows():
                test_type = tests.get(index,'')
                p = None
                if test_type == 'ttest':
                    t, p = ttest_ind(on[index], not_on[index], nan_policy='omit')
                if test_type == 'chi2':
                    table = pd.crosstab(data[d], data[index])
                    chi2, p, dof, ex = chi2_contingency(table)
                pvals.append(p)
            tbl[raw_name] = pvals
            if correct:
                tbl[corr_name] = None
                w = ~tbl[raw_name].isna()
                r, corr, s, b = multipletests(tbl.loc[w,raw_name], method='bonferroni')
                tbl.loc[w,corr_name] = corr
    return tbl

def round_sig(x, sig=2):
    """Round x to sig significant figures."""
    return round(x, sig-int(floor(log10(abs(x))))-1)

def get_one_LR_summary(factors, data, y, significance_level = 0.05, add_constant = True, verbose=False):
    """
    
    Parameters
    ----------

    Returns
    _______

    """

    X = data[factors]

    if add_constant:
        X = sm.add_constant(X)
        
    X = X.astype(float)
    
    #model = sm.OLS(y, X).fit() #linear regression
    model = sm.Logit(y, X).fit()
    params = model.params
    conf = model.conf_int()
    conf['OR'] = params
    conf.columns = ['Lower 95%CI', 'Upper 95%CI', 'OR']
    or_ci = np.exp(conf)
    or_ci = or_ci.round(2)
    or_ci['raw P-value'] = model.pvalues
    or_ci['Significant'] = or_ci['raw P-value'] < significance_level
    if verbose:
        print(model.summary())
        print()
        print(or_ci)
    return or_ci

def get_LR_summary(model_defs, data, y, significance_level=0.05, add_constant=True, verbose=False):
    """
    
    Parameters
    ----------

    Returns
    _______

    """
    res = []
    for model_name, model_factors in model_defs.items():
        r = get_one_LR_summary(model_factors, data, y, significance_level, add_constant, verbose)
        r['Model'] = model_name
        res.append(r)
    result = pd.concat(res, axis=0)
    return result