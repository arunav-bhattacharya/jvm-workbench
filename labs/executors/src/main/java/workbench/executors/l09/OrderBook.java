package workbench.executors.l09;

import java.util.List;

/** Fetches the order lines of one table for the day. Blocking: it queries the database. */
public interface OrderBook {
    List<String> lines(String table);
}
