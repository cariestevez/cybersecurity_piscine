IMAGE_NAME = onion_skin
CONTAINER_NAME = ft_onion

all: build run

build:
	@docker build -t $(IMAGE_NAME) .

run:
	@docker run -d --name $(CONTAINER_NAME) $(IMAGE_NAME)

rebuild: clean build

clean:
	@docker ps -q -f name=ft_onion && docker stop $(CONTAINER_NAME) || echo "No container to stop"
	@docker ps -aq -f name=ft_onion && docker rm $(CONTAINER_NAME) || echo "No container to remove"
	@docker rmi $(IMAGE_NAME) || echo "No image to remove"
