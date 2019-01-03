import re
import pandas as pd
def souhu_txt_to_parquet():
    data_dict={}
    all_article=[]
    filter_pattern='<doc>|</doc>|<url>|</url>|<docno>|</docno>|<content>|</content>'
    with open('../news/news_sohusite_xml.txt',encoding='gbk',errors='ignore') as fileself:
        for each in fileself:
            each=each.strip('\r\n')
            if each.startswith('<doc>'):#and not each.startswith('</doc>'):
                each_article = {}
            # each=re.sub('<doc>|<url>|</url>|<docno>|</docno>|<content>|</content>|<contenttitle>|</contenttitle>','',each)
            # each_article.append(each)
            url_pattern=re.search('<url>(.*)</url>',each)
            docno_pattern=re.search('<docno>(.*)</docno>',each)
            content_pattern=re.search('<content>(.*)</content>',each)
            title_pattern = re.search('<contenttitle>(.*)</contenttitle>', each)

            if url_pattern:
                each_article['url'] = url_pattern.group(1)
            if docno_pattern:
                each_article['docno'] = docno_pattern.group(1)
            if title_pattern:
                each_article['title']=title_pattern.group(1)
            if content_pattern:
                each_article['content'] = content_pattern.group(1)


            if each.startswith('</doc>'):
                all_article.append(each_article)

            #
            # print(each)

    df=pd.DataFrame(all_article)
    df.to_parquet('../news/souhu.parquet.gzip',compression='gzip')


    for each in df.head().iterrows():
        print(each)
    # print(df.head(1))

def lcsts_txt_to_parquet():
    data_dict={}
    all_article=[]
    filter_pattern='<doc>|</doc>|<url>|</url>|<docno>|</docno>|<content>|</content>'
    with open('/Users/ozintel/Downloads/LCSTS/DATA/PART_I.txt',encoding='utf8',errors='ignore') as fileself:
        for each in fileself:
            each=each.strip('\r\n')
            if each.startswith('<doc id='):
                each_article_str = ''
                each_article_dic={}
            if not each.startswith('</doc>'):
                each_article_str+=each
            # each=re.sub('<doc>|<url>|</url>|<docno>|</docno>|<content>|</content>|<contenttitle>|</contenttitle>','',each)
            # each_article.append(each)
            if each.startswith('</doc>'):
                # print('each_article',each_article_str)

                score_pattern=re.search('<human_label>(.*)</human_label>',each_article_str)
                content_pattern = re.search('<short_text>(.*)</short_text>', each_article_str)
                title_pattern = re.search('<summary>(.*)</summary>', each_article_str)

                if score_pattern:
                    each_article_dic['score'] = score_pattern.group(1).strip(' ')
                if content_pattern:
                    each_article_dic['content'] = content_pattern.group(1).strip(' ')
                if title_pattern:
                    each_article_dic['title'] = title_pattern.group(1).strip(' ')

                all_article.append(each_article_dic)

    df=pd.DataFrame(all_article)
    # df.to_csv('../news/temp.csv')
    # df.to_parquet('../news/lcsts_part1.parquet.gzip',compression='gzip')


    for each in df.head().iterrows():
        print(each)
    # print(df.head(1))

def read_parquet():
    path1='../news/souhu.parquet.gzip'
    path2='../news/lcsts_part1.parquet.gzip'
    df=pd.read_parquet(path1)
    print(df.shape)##souhu(1411996, 4)  lcsts1 (2400591, 2)
    for each in df.head(10).values:#.iterrows():
        print(each)


if __name__=='__main__':
    read_parquet()
    # souhu_txt_to_parquet()
    # lcsts_txt_to_parquet()
