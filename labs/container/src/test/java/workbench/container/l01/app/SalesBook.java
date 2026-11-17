package workbench.container.l01.app;

import workbench.container.l01.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class SalesBook {
    private final List<String> lines = new ArrayList<>();

    public synchronized void add(String line) {
        lines.add(line);
    }

    public synchronized List<String> lines() {
        return List.copyOf(lines);
    }
}
