package workbench.container.l01.app;

import workbench.container.l01.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class Ledger {
    private final List<String> lines = new ArrayList<>();

    public synchronized void post(String line) {
        lines.add(line);
    }

    public synchronized List<String> lines() {
        return List.copyOf(lines);
    }
}
