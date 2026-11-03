# SAVE DATABASE
# JD.title = obj.job_title
# JD.rawtext = collect(obj.requirements, obj.responsibilities)
# JD.cleantext = retrieve(obj.rawtext) → List[word:str]
# JD.JobSkills = obj.job_skills → List[word:str]
from app.data.JDs.transformation.main import main as transformation_main
# from app.crud.jd import JD as JDModel
# from app.crud.jd_skill import JDSkill as JDSkillModel

def main() -> None:
    transformation_main()
    print("Hello world from loading.main.py")
    
if __name__ == "__main__":
    main()