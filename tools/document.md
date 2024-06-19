# 100X Scaling: How Figma Scaled its Databases

## Intro 

Figma, a collaborative design platform, has been on a wild growth ride for the last few years. Its user base has grown by almost 200% since 2018, attracting around 3 million monthly users.

As more and more users have hopped on board, the infrastructure team found themselves in a spot. They needed a quick way to scale their databases to keep up with the increasing demand.

The database stack is like the backbone of Figma. It stores and manages all the important metadata, like permissions, file info, and comments. And it ended up growing a whopping 100x since 2020! 

That's a good problem to have, but it also meant the team had to get creative.

In this article, we'll dive into Figma's database scaling journey. We'll explore the challenges they faced, the decisions they made, and the innovative solutions they came up with. By the end, you'll better understand what it takes to scale databases for a rapidly growing company like Figma.


# The Initial State of Figma’s Database Stack

In 2020, Figma still used a single, large Amazon RDS database to persist most of the metadata. While it handled things quite well, one machine had its limits. 

During peak traffic, the CPU utilization was above 65% resulting in unpredictable database latencies.

While complete saturation was far away, the infrastructure team at Figma wanted to proactively identify and fix any scalability issues. They started with a few tactical fixes such as:

Upgrade the database to the largest instance available (from r5.12xlarge to r5.24xlarge).

Create multiple read replicas to scale read traffic.

Establish new databases for new use cases to limit the growth of the original database.

Add PgBouncer as a connection pooler to limit the impact of a growing number of connections.

These fixes gave them an additional year of runway but there were still limitations:

Based on the database traffic, they learned that write operations contributed a major portion of the overall utilization. 

All read operations could not be moved to replicas because certain use cases were sensitive to the impact of replication lag.

It was clear that they needed a longer-term solution.

## The First Step: Vertical Partitioning

When Figma's infrastructure team realized they needed to scale their databases, they couldn't just shut everything down and start from scratch. They needed a solution to keep Figma running smoothly while they worked on the problem. 

That's where vertical partitioning came in.

Think of vertical partitioning as reorganizing your wardrobe. Instead of having one big pile of mess, you split things into separate sections. In database terms, it means moving certain tables to separate databases.

For Figma, vertical partitioning was a lifesaver. It allowed them to move high-traffic, related tables like those for “Figma Files” and “Organizations” into their separate databases. This provided some much-needed breathing room.

To identify the tables for partitioning, Figma considered two factors:

Impact: Moving the tables should move a significant portion of the workload.

Isolation: The tables should not be strongly connected to other tables.

For measuring impact, they looked at average active sessions (AAS) for queries. This stat describes the average number of active threads dedicated to a given query at a certain point in time.

Measuring isolation was a little more tricky. They used runtime validators that hooked into ActiveRecord, their Ruby ORM. The validators sent production query and transaction information to Snowflake for analysis, helping them identify tables that were ideal for partitioning based on query patterns and table relationships.

Once the tables were identified, Figma needed to migrate them between databases without downtime. They set the following goals for their migration solution:

Limit potential availability impact to less than 1 minute.

Automate the procedure so it is easily repeatable.

Have the ability to undo a recent partition.

Since they couldn’t find a pre-built solution that could meet these requirements, Figma built an in-house solution. At a high level, it worked as follows:

Prepared client applications to query from multiple database partitions.

Replicated tables from the original database to a new database until the replication lag was near 0.

Paused activity on the original database.

Waited for databases to synchronize.

Rerouted query traffic to the new database.

Resumed activity.

To make the migration to partitioned databases smoother, they created separate PgBouncer services to split the traffic virtually. Security groups were implemented to ensure that only PgBouncers could directly access the database.

Partitioning the PgBouncer layer first gave some cushion to the clients to route the queries incorrectly since all PgBouncer instances initially had the same target database. During this time, the team could also detect the routing mismatches and make the necessary corrections.

The below diagram shows this process of migration.

## Implementing Replication


Data replication is a great way to scale the read operations for your database. When it came to replicating data for vertical partitioning, Figma had two options in Postgres: streaming replication or logical replication.

They chose logical replication for 3 main reasons:

Logical replication allowed them to port over a subset of tables so that they could start with a much smaller storage footprint in the destination database.

It enabled them to replicate data into a database running a different Postgres major version.

Lastly, it allowed them to set up reverse replication to roll back the operation if needed.

However, logical replication was slow. The initial data copy could take days or even weeks to complete. 

Figma desperately wanted to avoid this lengthy process, not only to minimize the window for replication failure but also to reduce the cost of restarting if something went wrong.

But what made the process so slow?

The culprit was how Postgres maintains indexes in the destination database. While the replication process copies rows in bulk, it also updates the indexes one row at a time. By removing indexes in the destination database and rebuilding them after the data copy, Figma reduced the copy time to a matter of hours.

## Need for Horizontal Scaling

As Figma's user base and feature set grew, so did the demands on their databases. 

Despite their best efforts, vertical partitioning had limitations, especially for Figma’s largest tables. Some tables contained several terabytes of data and billions of rows, making them too large for a single database.

A couple of problems were especially prominent:

Postgres Vacuum Issue: Vacuuming is an essential background process in Postgres that reclaims storage occupied by deleted or obsolete rows. Without regular vacuuming, the database would eventually run out of transaction IDs and grind to a halt. However, vacuuming large tables can be resource-intensive and cause performance issues and downtime.

Max IO Operations Per Second: Figma’s highest write tables were growing so quickly that they would soon exceed the max IOPS limit of Amazon’s RDS.

For a better perspective, imagine a library with a rapidly growing collection of books. Initially, the library might cope by adding more shelves (vertical partitioning). But eventually, the building itself will run out of space. No matter how efficiently you arrange the shelves, you can’t fit an infinite number of books in a single building. That’s when you need to start thinking about opening branch libraries.

This is the approach of horizontal sharding.

For Figma, horizontal sharding was a way to split large tables across multiple physical databases, allowing them to scale beyond the limits of a single machine. 

The below diagram shows this approach:
However, horizontal sharding is a complex process that comes with its own set of challenges:

Some SQL queries become inefficient to support.

Application code must be updated to route queries efficiently to the correct shard.

Schema changes must be coordinated across all shards. 

Postgres can no longer enforce foreign keys and globally unique indexes.

Transactions span multiple shards, which means Postgres cannot be used to enforce transactionality.

## Exploring Alternative Solutions

The engineering team at Figma evaluated alternative SQL options such as CockroachDB, TiDB, Spanner, and Vitess as well as NoSQL databases.

Eventually, however, they decided to build a horizontally sharded solution on top of their existing vertically partitioned RDS Postgres infrastructure. 

There were multiple reasons for taking this decision:

They could leverage their existing expertise with RDS Postgres, which they had been running reliably for years.

They could tailor the solution to Figma’s specific needs, rather than adapting their application to fit a generic sharding solution.

In case of any issues, they could easily roll back to their unsharded Postgres databases.

They did not need to change their complex relational data model built on top of Postgres architecture to a new approach like NoSQL. This allowed the teams to continue building new features.

## Figma’s Unique Sharding Implementation

Figma’s approach to horizontal sharding was tailored to their specific needs as well as the existing architecture. They made some unusual design choices that set their implementation apart from other common solutions.

Let’s look at the key components of Figma’s sharding approach:

## Colos (Colocations) for Grouping Related Tables

Figma introduced the concept of “colos” or colocations, which are a group of related tables that share the same sharding key and physical sharding layout. 

To create the colos, they selected a handful of sharding keys like UserId, FileId, or OrgID. Almost every table at Figma could be sharded using one of these keys.

This provides a friendly abstraction for developers to interact with horizontally sharded tables. 

Tables within a colo support cross-table joins and full transactions when restricted to a single sharding key. Most application code already interacted with the database in a similar way, which minimized the work required by applications to make a table ready for horizontal sharding.

The below diagram shows the concept of colos:

## Logical Sharding vs Physical Sharding

Figma separated the concept of “logical sharding” at the application layer from “physical sharding” at the Postgres layer.

Logical sharding involves creating multiple views per table, each corresponding to a subset of data in a given shard. All reads and writes to the table are sent through these views, making the table appear horizontally sharded even though the data is physically located on a single database host.

This separation allowed Figma to decouple the two parts of their migration and implement them independently. They could perform a safer and lower-risk logical sharding rollout before executing the riskier distributed physical sharding. 

Rolling back logical sharding was a simple configuration change, whereas rolling back physical shard operations would require more complex coordination to ensure data consistency.

## DBProxy Query Engine for Routing and Query Execution

To support horizontal sharding, the Figma engineering team built a new service named DBProxy that sits between the application and connection pooling layers such as the PGBouncer.

DBProxy includes a lightweight query engine capable of parsing and executing horizontally sharded queries. It consists of three main components:

A query parser that reads the SQL sent by the application and transforms it into an Abstract Syntax Tree (AST).

A logical planner that parses the AST, extracts the query type (insert, update, etc.), and logical shard IDs from the query plan.

A physical planner that maps the query from logical shard IDs to physical databases and rewrites queries to execute on the appropriate physical shard.

The below diagram shows the practical use of these three components within the query processing workflow.

There are always trade-offs when it comes to queries in a horizontally sharded world. Queries for a single shard key are relatively easy to implement. The query engine just needs to extract the shard key and route the query to the appropriate physical database.

However, if the query does not contain a sharding key, the query engine has to perform a more complex “scatter-gather” operation. This operation is similar to a hide-and-seek game where you send the query to every shard (scatter), and then piece together answers from each shard (gather). 

The below diagram shows how single-shard queries work when compared to scatter-gather queries.

As you can see, this increases the load on the database, and having too many scatter-gather queries can hurt horizontal scalability.

To manage things better, DBProxy handles load-shedding, transaction support, database topology management, and improved observability.

## Shadow Application Readiness Framework

Figma added a “shadow application readiness” framework capable of predicting how live production traffic would behave under different potential sharding keys. 

This framework helped them keep the DBProxy simple while reducing the work required for the application developers in rewriting unsupported queries. 

All the queries and associated plans are logged to a Snowflake database, where they can run offline analysis. Based on the data collected, they were able to pick a query language that supported the most common 90% of queries while avoiding the worst-case complexity in the query engine.

## Conclusion

Figma’s infrastructure team shipped their first horizontally sharded table in September 2023, marking a significant milestone in their database scaling journey.

It was a successful implementation with minimal impact on availability. Also, the team observed no regressions in latency or availability after the sharding operation.

Figma’s ultimate goal is to horizontally shard every table in their database and achieve near-infinite scalability. They have identified several challenges that need to be solved such as:

Supporting horizontally sharded schema updates

Generating globally unique IDs for horizontally sharded primary keys

Implementing atomic cross-shard transactions for business-critical use cases.

Enabling distributed globally unique indexes.

Developing an ORM model to improve developer velocity

Automatic reshard operations to enable shard splits at the click of a button.

Lastly, after achieving a sufficient runway, they also plan to reassess their current approach of using in-house RDS horizontal sharding versus switching to an open-source or managed alternative in the future.


