CXX      = g++
CXXFLAGS = -O2 -fopenmp
TARGET   = main.o

all: $(TARGET)

$(TARGET): main.cpp
	$(CXX) $(CXXFLAGS) -o $(TARGET) main.cpp

run: $(TARGET)
	./$(TARGET)

plot: run
	python3 plot_table.py

clean:
	rm -f $(TARGET) results.csv task1_results.png