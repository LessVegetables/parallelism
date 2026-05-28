CXX      = g++
CXXFLAGS = -O2 -fopenmp
TARGET   = task1.o

all: $(TARGET)

$(TARGET): task_1.cpp
	$(CXX) $(CXXFLAGS) -o $(TARGET) task_1.cpp

run: $(TARGET)
	./$(TARGET)

plot: run
	python3 plot_table.py

clean:
	rm -f $(TARGET) results.csv task1_results.png