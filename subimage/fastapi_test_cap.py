import requests
import json

def test(caption):
    datas = json.dumps({'caption': caption})
    rec = requests.post("http://0.0.0.0:12346/cap_seg", data=datas) 
    return rec.text
 
result= test('Figure 10 Brachiopoda and trilobite from the Kuanyinchiao Bed (Hirnantian Stage) at Wangjiawan. 1, 2, 5, 6. Kinnella kielanae, 1, 5, x 6.8, x 7.7 (NIGP136755); 2, 6, x 7.1 and x 12.8 (136756). 3, 4, 7. Paromalomena polonica, 3, x 5.4 (136757); 4, 7, x 5.3, x 9.3 (136758-9). 8. Plectothyrella crassicosta, x 2.9 (136760). 9, 10. Dysprosorthis sinensis, x 7.1, x 4.2 (136761-2). 11. Draborthis caelebs, x 3.6 (136763). 12. Triplesia yichangensis, x 2.9 (136764). 13. Dalmanella testudinaria, x 5.8 (136765). 14, 16. Cliftonia oxoplecioides, x 2.7, x 4.7 (136766-7). 15. Aegiromena ultima, x 7.9 (136768). 17, 21. Eostropheodonta parvicostellata, x 4.4, x 1.8 (136769-70). 18. Hindella crassa incipiens, x 1.8 (136771). 19. Leptaena trifidum, x 1.6 (136772). 20. Dalmanitina sp., x 3.7 (136773). 22, 23. Hirnantia sagittifera, x 1.7, x 2.1 (136774-5).')
print(result)