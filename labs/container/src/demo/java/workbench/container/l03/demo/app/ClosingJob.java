package workbench.container.l03.demo.app;

import workbench.container.l03.Component;
import workbench.container.l03.ShowCloser;

@Component
public class ClosingJob {
    private final ShowCloser closer;
    private final SalesBook book;

    public ClosingJob(ShowCloser closer, SalesBook book) {
        this.closer = closer;
        this.book = book;
    }

    public String run(String night) {
        String result = closer.close(night);
        book.add(result);
        return result;
    }
}
