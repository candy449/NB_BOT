from pydantic import BaseSettings


class Config(BaseSettings):
    # SVN配置
    svn_url: str = "https://ml.svn.oa.mt:8833/svn/mlproj2017/trunk/Assets/Document/HeroCostume.csv"  # SVN文件URL
    svn_username: str = "haideehu@moonton.com"  # SVN用户名
    svn_password: str = "Huzhe313!!!"  # SVN密码

    # 表格配置
    search_column: str = "皮肤名"  # 要搜索的列名
    return_columns: list = ["英雄ID", "皮肤ID（单个英雄皮肤id间隔30），1001-3999为皮肤；14001-14500翻新英雄默认皮肤；45011-49999指挥官皮肤；600000-699999染色皮肤id段", "收藏品质(1-A及以下；2-A+；3-S级；4-大抽奖、年度星光；5-SP及IP联动；6-S+)"]  # 要返回的列名

    class Config:
        extra = "ignore"