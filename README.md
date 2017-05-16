# graph-stream-generator

The Graph Stream Generator (GSG) generates multiple streams of graph vertices and edges according to subgraph patterns that can be partitioned across different streams.

Author: Larry Holder, School of EECS, Washington State University, email: holder@eecs.wsu.edu.

##Input File

The input file is in JSON format. An example is in the file input.json.
There are a few required global parameters to the Graph Stream Generator (GSG).

* **numStreams**: The number of graph streams to generate.
* **secondsPerUnitTime**: GSG schedules and generates vertices and edges based on integer time units. This parameter indicates how many seconds occur in one GSG time unit.
* **startTime**: The date and time that the generation starts. Format is "YYYY-MM-DD HH:MM:SS".
* **duration**: Number of time units for this generation.
* **outputTimeFormat**: One of "units", "seconds" or "datetime". Controls how the time stamps on vertices and edges are output.
* **outputFilePrefix**: Base name for output files. A file called *outputFilePrefix*-s*N* is created for each stream 1 to *N*, and a file called *outputFilePrefix*-insts is created to contain the instances of tracked patterns.
* **patterns**: Array of patterns to be included in the streams. See below for a description of a pattern.

### Pattern

A pattern describes a subgraph (set of vertices and edges) that are probabilistically-added to the graph streams. Vertices can be new, or drawn from earlier in the stream. Edges are assigned to a specific stream and scheduled according to a uniform offset range from the initial time unit when the pattern is chosen. Each vertex and edge can have a set of attribute-value pairs. Specifically, a pattern consists of the following properties (all required):

* **id**: String identifier for this pattern, which is used to identify pattern instances in the output instances file.
* **track**: Whether or not this pattern's instances should be output to the instances file. Value is "true" or "false".
* **probability**: The probability at each time unit that this pattern will be added to the graph streams. Value is [0.0,1.0], as a string.
* **vertices**: Array of vertex entries, described below.
* **edges**: Array of edge entries, described below.

####Vertex

A vertex appearing in the *vertices* array of a pattern consists of the following properties in a JSON object.

* **id**: String identifier for this vertex.
* **new**: Whether this vertex should be created as new ("true"), or mapped to a vertex already written to the stream ("false"). The stream is chosen based on the streams of the incident edges, all of which must be assigned to the same stream.
* **attributes**: A JSON object of name/value pairs, where both the name and value are strings. Attributes are not interpreted in any way, but merely copied to the streams along with the vertex instances. If this vertex is not new, then attributes are ignored (and can be omitted), because the existing attributes on the old vertex will be used.

A new vertex is written to a stream just before the earliest edge that involves this vertex is written to the stream. If edges assigned to different streams connect to the same vertex, then that same vertex is written to each stream.

####Edge

An edge appearing in the *edges* array of a pattern consists of the following properties in a JSON object.

* **id**: String identifier for this edge.
* **source**: Vertex identifier string for the edge's source vertex.
* **target**: Vertex identifier string for the edge's target vertex.
* **directed**: Boolean as to whether the edge is directed from source to target ("true"), or undirected ("false").
* **minOffset**: A non-negative integer (as a string) representing the minimum number of time units after the pattern is chosen that this edge appears in the stream. The actual offset is uniformly distributed over [minOffset,maxOffset].
* **maxOffset**: A non-negative integer (as a string) representing the maximum number of time units after the pattern is chosen that this edge appears in the stream. The actual offset is uniformly distributed over [minOffset,maxOffset].
* **streamNum**: The stream to which this edge (and it's vertices) will be written. Must be an integer (as a string) in the range [1,*numStreams*].
* **attributes**: A JSON object of name/value pairs, where both the name and value are strings. Attributes are not interpreted in any way, but merely copied to the streams along with the edge instances.

Each edge in a pattern can be assigned to a different stream, except that edges connected to a non-new vertex must all be assigned to the same stream. Using this technique, a pattern can be divided up across multiple streams. This is one of the main goals of GSG, that is, to provide test data to see if a graph mining system can find the full pattern by analyzing (or fusing) the individual streams. In terms of fusion, the streams can be easily fused together into one large graph, using the vertex ids as anchors. That is, two vertices from two different streams having the same id, represent the same vertex (or entity).

In the event that vertices and edges are scheduled to appear beyond the *duration* of the stream generation, stream generation will continue until all scheduled vertices and edges are written to streams. No new patterns are trigger beyond the *duration* of the stream generation.

##Output Stream Files

A file named *outputFilePrefix*-s*N* is created for each stream 1 to *N*. Each stream file contains a JSON array of vertex and edge instances, as described below.

###Vertex Instance

A vertex instance is a JSON object with name "vertex" and whose value is a JSON object with the following properties.

* **id**: An integer id (as a string) automatically generated by GSG that uniquely identifies this vertex in all streams in which it appears, and in the instances file if part of an instance of a tracked pattern.
* **attributes**: A JSON object of name/value pairs, where both the name and value are strings. These are merely copied from the attributes defined for this vertex in the input pattern.
* **timeStamp**: A string representing the time at which this vertex was written to the stream. The format is dictated by the *outputTimeFormat* parameter.

###Edge Instance

An edge instance is a JSON object with name "edge" and whose value is a JSON
object with the following properties.

* **id**: An integer id (as a string) automatically generated by GSG that uniquely identifies this edge in this stream, and in the instances file if part of an instance of a tracked pattern.
* **source**: Vertex identifier string for the edge's source vertex instance.
* **target**: Vertex identifier string for the edge's target vertex instance.
* **directed**: Whether the edge is directed from source to target ("true"), or undirected ("false"). Same as defined in the input pattern.
* **attributes**: A JSON object of name/value pairs, where both the name and value are strings. These are merely copied from the attributes defined for this edge in the input pattern.
* **timeStamp**: A string representing the time at which this edge was written
 to the stream. The format is dictated by the *outputTimeFormat* parameter.

##Output Instances File

A single file named *outputFilePrefix*-insts is created that contains a JSON array of pattern instances for all tracked patterns. Each pattern instance is a JSON object with the following properties.

* **patternId**: The pattern identifier string from the input file pattern.
* **vertexIds**: An array of vertex instance Id's (as strings) of all vertices contained in this pattern instance.
* **edgeIds**: An array of edge instance Id's (as strings) of all edges contained in this pattern instance.

The instances file provides the ground truth of all the full patterns that appear across all the graph streams.

##Questions?

Contact: Dr. Larry Holder, School of EECS, Washington State University, email: holder@eecs.wsu.edu.

