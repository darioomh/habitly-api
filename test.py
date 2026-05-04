import uvicorn

if __name__ == "__main__":
    print("Iniciando Habitly API...")
    print("Ve a: http://localhost:8001/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)