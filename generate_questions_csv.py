import csv

questions = [
["Die Aufgabe war sehr ___.","schwierig","kompliziert","anspruchsvoll","mühsam","anspruchsvoll","Implies the task requires high intellectual demand rather than simple difficulty.","B2"],
["Wir müssen eine Entscheidung ___.","machen","treffen","bilden","nehmen","treffen","Fixed German collocation: eine Entscheidung treffen.","A2"],
["Das Problem ist ziemlich ___.","komplex","simpel","oberflächlich","locker","komplex","Complex means multi-layered or involving many factors.","B2"],
["Er hat eine große ___.","Verantwortung","Aufgabe","Pflicht","Schuld","Verantwortung","Refers to responsibility rather than simply a task.","B1"],
["Sie hat mir einen guten ___ gegeben.","Hinweis","Rat","Idee","Vorschlag","Rat","'Rat geben' means to give advice.","A2"],
["Das Projekt wurde ___.","umgesetzt","gemacht","gebaut","erzeugt","umgesetzt","Formal verb meaning implemented or executed.","B2"],
["Die Lösung ist nicht ganz ___.","offensichtlich","klar","sichtbar","laut","offensichtlich","Means evident or self-evident.","B1"],
["Wir müssen das Thema ___.","behandeln","nehmen","greifen","ziehen","behandeln","Formal verb meaning to deal with a topic.","B2"],
["Seine Argumente sind sehr ___.","überzeugend","stark","laut","sicher","überzeugend","Arguments that persuade logically.","B2"],
["Sie hat eine wichtige Rolle ___.","gespielt","gemacht","gehabt","gebaut","gespielt","Fixed expression: eine Rolle spielen.","A2"],
["Das Unternehmen hat großen ___.","Gewinn","Erfolg","Vorteil","Nutzen","Erfolg","Success context rather than financial profit.","B1"],
["Das ist eine ___ Frage.","schwierige","komplexe","zentrale","harte","zentrale","Means key or central to the issue.","B2"],
["Wir sollten das Problem ___.","lösen","reparieren","fixieren","machen","lösen","Solve a problem intellectually.","A2"],
["Das Ergebnis war sehr ___.","überraschend","plötzlich","neu","interessant","überraschend","Unexpected outcome.","B1"],
["Er hat viel ___ gesammelt.","Erfahrung","Wissen","Kenntnis","Bildung","Erfahrung","Experience gained over time.","B1"],
]

with open("questions.csv","w",newline="",encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["sentence","option_a","option_b","option_c","option_d","correct_answer","explanation","level"])
    writer.writerows(questions)

print("questions.csv created successfully")