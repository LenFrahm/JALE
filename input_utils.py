import sys
import pandas as pd
import numpy as np
from tal2icbm_spm import tal2icbm_spm
from template import affine

def load_excel(filepath):
    try:
        df = pd.read_excel(filepath)
    except FileNotFoundError:
        print(f"File '{filepath}' not found.")
        sys.exit()
    except ValueError:
        print(f"Error reading Excel file '{filepath}'. Make sure it's a valid Excel file.")
        sys.exit()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit()
    df.dropna(inplace=True, how='all')
    return df

def check_coordinates_are_numbers(df):
    all_coord_numbers_flag = 1
    for coord_col in ['x', 'y', 'z']:
        coord_col_all_number_bool = pd.api.types.is_float_dtype(df[coord_col])
        if coord_col_all_number_bool == False:
            all_coord_numbers_flag = 0
            coerced_column = pd.to_numeric(df[coord_col], errors='coerce')
            non_integer_mask = (coerced_column.isnull()) | (coerced_column % 1 != 0)
            rows_with_errors = df.index[non_integer_mask]
            print(f'Non-numeric Coordinates in column {coord_col}: {rows_with_errors.values + 2}')

    if all_coord_numbers_flag == False:
        exit()
    else:
        return df.reset_index(drop=True)

def concat_coordinates(exp_info):
    article_rows = exp_info.index[exp_info['Articles'].notnull()].tolist()
    end_of_articles = [x - 1 for x in article_rows]
    end_of_articles.pop(0)
    end_of_articles.append(exp_info.shape[0])

    exp_info_firstlines = exp_info.loc[article_rows].reset_index(drop=True)
    exp_info_firstlines = exp_info_firstlines.drop(['x','y','z'], axis=1)

    exp_info_firstlines['Coordinates_mm'] = np.nan
    exp_info_firstlines['Coordinates_mm'] = exp_info_firstlines['Coordinates_mm'].astype(object)
    exp_info_firstlines['NumberOfFoci'] = np.nan

    for i in range(len(article_rows)):
        x = exp_info.loc[article_rows[i]:end_of_articles[i]].x.values
        y = exp_info.loc[article_rows[i]:end_of_articles[i]].y.values
        z = exp_info.loc[article_rows[i]:end_of_articles[i]].z.values
        
        coordinate_array = np.array((x,y,z)).T
        exp_info_firstlines.at[i,'Coordinates_mm'] = coordinate_array
        exp_info_firstlines.loc[i,'NumberOfFoci'] = len(x)
    
    return exp_info_firstlines

def concat_tags(exp_info):
    exp_info['Tags'] = exp_info.apply(lambda row: row.iloc[6:].dropna().str.lower().str.strip().values, axis=1)
    exp_info = exp_info.drop(exp_info.iloc[:, 6:-1],axis = 1)
    return exp_info

def convert_tal_2_mni(exp_info):
    exp_info.loc[exp_info.CoordinateSpace == "TAL", "Coordinates_mm"] = exp_info[exp_info.CoordinateSpace == "TAL"].apply(
            lambda row: tal2icbm_spm(row.Coordinates_mm), axis=1)
    return exp_info

def transform_coordinates_to_voxel_space(exp_info):
    padded_xyz = exp_info.apply(
        lambda row: np.pad(row.Coordinates_mm, ((0,0),(0,1)), constant_values=[1]), axis=1).values
    exp_info['Coordinates'] = [np.ceil(np.dot(np.linalg.inv(affine), xyzmm.T))[:3].T.astype(int) for xyzmm in padded_xyz]

    thresholds = [91,109,91]
    out_of_bounds_larger = exp_info.apply(lambda row: np.any(row.Coordinates > thresholds, axis=0), axis=1).values
    out_of_bounds_larger = [i for sublist in out_of_bounds_larger for i in sublist]

    out_of_bounds_smaller = exp_info.apply(lambda row: np.any(row.Coordinates < 0, axis=0), axis=1).values
    out_of_bounds_smaller = [i for sublist in out_of_bounds_smaller for i in sublist]
    
    if (True in out_of_bounds_larger) or (True in out_of_bounds_smaller):
        print('WARNING: Coordinate detected outside of Brain boundaries!')
    return exp_info

def create_tasks_table(exp_info):
    tasks = pd.DataFrame(columns=['Name', 'Num_Exp', 'Who', 'TotalSubjects', 'ExpIndex'])
    task_names, task_counts = np.unique(np.hstack(exp_info.Tags), return_counts=True)
    tasks.Name = task_names
    tasks.Num_Exp = task_counts

    task_exp_idxs = []
    for count, task in enumerate(task_names):
        task_exp_idxs = exp_info.index[
            exp_info.apply(lambda row: np.any(row.Tags == task), axis=1)].to_list()
        tasks.at[count, 'ExpIndex'] = task_exp_idxs
        tasks.at[count, 'Who'] = exp_info.loc[task_exp_idxs, 'Articles'].values
        tasks.at[count, 'TotalSubjects'] = np.sum(exp_info.loc[task_exp_idxs, 'Subjects'].values)

    tasks.loc[len(tasks)] = ['all',
                             exp_info.shape[0],
                             exp_info.Articles.values,
                             np.sum(exp_info.Subjects.values),
                             list(range(exp_info.shape[0]))]
    tasks = tasks.sort_values(by='Num_Exp', ascending=False).reset_index(drop=True)
    
    return tasks