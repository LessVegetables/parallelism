CXX      = g++
CXXFLAGS = -O2 -fopenmp
TARGET   = lab2

all: $(TARGET)

$(TARGET): lab2.cpp
	$(CXX) $(CXXFLAGS) -o $(TARGET) lab2.cpp

run: $(TARGET)
	./$(TARGET)

plot_table: run
	python3 plot_table.py	

plot_effectiveness: run
	python3 plot_effectiveness.py

plot: plot_table plot_effectiveness
	echo "done"
	

clean:
	rm -f $(TARGET) results_jacobi.csv results_jacobi.png