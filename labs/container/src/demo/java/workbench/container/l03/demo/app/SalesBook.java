package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@Component
public class SalesBook {
    private final List<String> lines = new CopyOnWriteArrayList<>();

    public void add(String line) { lines.add(line); }

    public int size() { return lines.size(); }
}
