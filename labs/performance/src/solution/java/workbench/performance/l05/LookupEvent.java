package workbench.performance.l05;

import jdk.jfr.Category;
import jdk.jfr.Description;
import jdk.jfr.Event;
import jdk.jfr.Label;
import jdk.jfr.Name;

@Name("workbench.Lookup")                           // the stable name tools and queries use
@Label("Document Lookup")                           // what JMC and `jfr view` show
@Category({"Workbench", "Reports"})
@Description("One lookup, timed from the call to the document store to its answer")
public class LookupEvent extends Event {
    @Label("Shelf")
    String shelf;

    @Label("Title")
    String title;

    @Label("Found")
    boolean found;
}
