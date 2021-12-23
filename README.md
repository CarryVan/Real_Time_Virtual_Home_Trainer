<div align="center">
<p>
   <a align="left" href="https://yhdev.com/xyz" target="_blank">
   <img width="350" height="550" src="https://user-images.githubusercontent.com/72462227/147232223-d014ba54-5a89-4d9a-bb1f-d5555292750f.jpg"></a>
</p>


<div align="center">


   <a href="https://github.com/CarryVan/Real_Time_Virtual_Home_Trainer">
   <img src="https://github.com/ultralytics/yolov5/releases/download/v1.0/logo-social-github.png" width="2%"/>
   </a>
</br>
Original Repository   
</div>

</br>
<p>
기존에 사용자와 분리되어 있던 Home Training App의 한계를 넘어</br>
사용자와 상호 작용하는 <b>Real-Time Virtual Home Trainer Application</b>을 소개합니다.🌟
</p>

</div>
<br>



## <div align="center">Quick Start Examples</div>

**Docker의 Container를 이용하여 간편하게 local server를 배포해볼 수 있습니다🚀**

</br>

<details open>
<summary>Deploy on Local Machine</summary>
</br>

📌 Local machine에서 실행할 시 모바일 기기의 카메라 접근은 **불가능**합니다.

📌 [**Python>=3.8.0**](https://www.python.org/) 버전이 요구됩니다. 

```bash
$ git clone https://github.com/boostcampaitech2/final-project-level3-cv-11.git 
$ cd final-project-level3-cv-11
$ pip install -r requirements.txt
$ uvicorn server:app --port 5000 --reload
```

-> http://127.0.0.1:5000 으로 접속할 수 있습니다.

</details>


<details open>
<summary>Deploy on Docker Container</summary>
</br>

📌`docker-compose.yml`파일을 사용해서 docker container를 띄워 local server를 구축합니다.

</br>

```bash
$ docker-compose up -d
```

-> https://{IPv4 Adress}:8080 으로 접속할 수 있습니다.
</details>
