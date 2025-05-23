import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
# Removed duplicate imports above
from sqlalchemy.orm import sessionmaker, joinedload
from models import Institution, Funder, Author, Paper, AuthorFunders # Ensure AuthorFunders is imported
from extensions import engine
# Imports for data acquisition
from data_acquisition import fetch_paper_data_from_openalex, add_paper_to_db

# --- Data Fetching ---
def fetch_data():
    """
    Fetches author data from the database, including their associated institutions and funders.
    It uses SQLAlchemy's joinedload to eagerly load related entities to prevent
    N+1 query problems.
    The session is closed after data fetching.
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        authors = (
            session.query(Author)
            .options(
                joinedload(Author.institutions), # Eagerly load institutions linked to authors
                # Eagerly load AuthorFunders associations, then the Funder object itself
                joinedload(Author.author_funder_associations).joinedload(AuthorFunders.funder) 
            )
            .all()
        )
        return authors
    finally:
        session.close() # Ensure session is closed in all cases

# --- Graph Creation ---
def create_network_graph(authors):
    """
    Creates a NetworkX graph from the list of author objects.
    Nodes are:
        - Authors (type: 'author')
        - Institutions (type: 'institution')
        - Funders (type: 'funder')
    Edges represent relationships:
        - Between authors and their institutions.
        - Between authors and their funders (via AuthorFunders).
    """
    G = nx.Graph()
    for author in authors:
        G.add_node(author.name, type="author") # Add author node
        for institution in author.institutions:
            G.add_node(institution.name, type="institution") # Add institution node
            G.add_edge(author.name, institution.name) # Add edge: author <-> institution
        
        # Access funders through the AuthorFunders association object
        for af_assoc in author.author_funder_associations:
            funder = af_assoc.funder # Get the actual Funder object
            if funder: # Ensure funder object exists
                G.add_node(funder.name, type="funder") # Add funder node
                G.add_edge(author.name, funder.name) # Add edge: author <-> funder
    return G

# --- Graph Visualization ---
def visualize_network(G, highlighted_nodes=None):
    """
    Visualizes the NetworkX graph using Matplotlib.
    - Nodes are positioned using the spring layout algorithm (nx.spring_layout).
    - Nodes are colored and sized based on their 'type' (author, institution, funder).
    - Edges are drawn in gray.
    - Node labels are displayed.
    - A legend is provided to distinguish node types.
    - If 'highlighted_nodes' are provided, they can be styled differently (optional, not implemented in this version).
    """
    if not G.nodes(): # If graph is empty (e.g. after filtering with no results)
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data to display for the current filter.", 
                horizontalalignment='center', verticalalignment='center', 
                transform=ax.transAxes)
        ax.axis("off")
        return fig

    pos = nx.spring_layout(G, k=0.15, iterations=20) # Position nodes using the spring layout
    fig, ax = plt.subplots(figsize=(14, 12)) # Create a Matplotlib figure and axes

    # Define more distinct node colors
    node_colors_map = {
        "author": "cornflowerblue",      # A clearer blue for authors
        "institution": "mediumseagreen", # A distinct green for institutions
        "funder": "orangered",           # A prominent color for funders
    }

    # Calculate node degrees for dynamic sizing
    degrees = dict(G.degree())
    base_size = 200  # Base size for nodes with zero or one connection
    scale_factor = 150 # How much size increases per degree

    # Store handles for legend
    legend_handles = []

    # Draw each node type separately to apply specific styles and for the legend
    for node_type, color in node_colors_map.items():
        nodelist = [n for n, attr in G.nodes(data=True) if attr.get("type") == node_type]
        if nodelist: # Only draw if there are nodes of this type
            # Calculate sizes for nodes in the current nodelist based on their degree
            node_sizes_list = [base_size + degrees.get(n, 0) * scale_factor for n in nodelist]
            
            handle = nx.draw_networkx_nodes(
                G,
                pos,
                nodelist=nodelist,
                node_size=node_sizes_list, # Use dynamic sizes
                node_color=color,
                label=node_type.capitalize(), # Capitalize for legend
                ax=ax,
                alpha=0.8 # Slightly transparent
            )
            if handle: 
                 legend_handles.append(handle)

    # Draw edges with default styling
    nx.draw_networkx_edges(G, pos, edge_color="lightgray", alpha=0.7, width=0.8, ax=ax) # Made edges lighter and thinner

    # Draw labels for all nodes
    nx.draw_networkx_labels(G, pos, font_size=8, ax=ax)

    ax.axis("off") # Turn off the axis border and ticks

    # Adding legend to distinguish node types if there are handles
    if legend_handles:
        ax.legend(handles=legend_handles, scatterpoints=1, title="Node Types")
    
    # Removed the on_hover Matplotlib event as it's not Streamlit-friendly
    return fig


# --- Streamlit App Main Flow ---
st.set_page_config(layout="wide") # Use wide layout for better graph display
st.title("Conflicts of Interest Network Explorer")

# Fetch data once
# This can be cached using st.cache_data for better performance on reruns
@st.cache_data 
def load_data():
    """Cached function to load author data."""
    return fetch_data()

authors_data = load_data()
main_graph = create_network_graph(authors_data)

# Sidebar for controls and information
st.sidebar.title("Controls & Info")
st.sidebar.markdown("## Graph Search")
search_query = st.sidebar.text_input("Search by name (author, institution, or funder):", key="search_input")

st.sidebar.markdown("---") # Separator
st.sidebar.markdown("## Add Paper via DOI")
doi_input = st.sidebar.text_input("Enter DOI (e.g., 10.1038/s41586-021-03491-6):", key="doi_input")

if st.sidebar.button("Fetch and Add Paper Data", key="fetch_doi_button"):
    if doi_input:
        st.sidebar.info(f"Fetching data for DOI: {doi_input}...")
        paper_schema_data = fetch_paper_data_from_openalex(doi_input)
        if paper_schema_data:
            add_paper_to_db(paper_schema_data)
            st.sidebar.success(f"Data for DOI: {doi_input} processed. Graph will refresh.")
            load_data.clear() # Invalidate cache to refresh graph
            # Clear the DOI input field after successful processing (optional)
            # st.session_state.doi_input = "" 
            # Trigger a rerun to reflect cache clearing and potential input clearing immediately
            st.experimental_rerun() 
        else:
            st.sidebar.error(f"Failed to fetch or process data for DOI: {doi_input}.")
    else:
        st.sidebar.warning("Please enter a DOI to fetch data.")

st.sidebar.markdown("---") # Separator

# Initialize display_graph to main_graph
display_graph = main_graph
filtered_nodes_info = [] # To store names and types of matched nodes

if search_query:
    # Filter nodes based on the search query (case-insensitive)
    # Also store the node name and type for sidebar display
    matched_nodes_in_graph = [
        (node, main_graph.nodes[node]['type']) for node in main_graph.nodes 
        if search_query.lower() in str(node).lower()
    ]

    if matched_nodes_in_graph:
        # Create a subgraph containing only the matched nodes and their direct neighbors
        nodes_for_subgraph = set()
        for node_name, _ in matched_nodes_in_graph:
            nodes_for_subgraph.add(node_name)
            nodes_for_subgraph.update(main_graph.neighbors(node_name)) # Add neighbors for context
        
        subgraph = main_graph.subgraph(list(nodes_for_subgraph))
        display_graph = subgraph
        filtered_nodes_info = matched_nodes_in_graph # For sidebar display
    else:
        st.sidebar.write("No matching nodes found for your query.")
        # display_graph will be empty or show "No data" via visualize_network
        display_graph = nx.Graph() # Create an empty graph

# Display information about matched nodes in the sidebar
if search_query and filtered_nodes_info:
    st.sidebar.subheader("Search Results:")
    if len(filtered_nodes_info) == 1:
        node_name, node_type = filtered_nodes_info[0]
        st.sidebar.info(f"Displaying details for: **{node_name}** (Type: {node_type.capitalize()})")
        
        # Display detailed connections for the uniquely identified node
        if node_name in display_graph: # Check if node is in the possibly smaller subgraph
            st.sidebar.markdown("**Connections in current view:**")
            connected_authors = []
            connected_institutions = []
            connected_funders = []

            for neighbor in display_graph.neighbors(node_name):
                neighbor_attr = display_graph.nodes[neighbor]
                if neighbor_attr.get("type") == "author":
                    connected_authors.append(neighbor)
                elif neighbor_attr.get("type") == "institution":
                    connected_institutions.append(neighbor)
                elif neighbor_attr.get("type") == "funder":
                    connected_funders.append(neighbor)
            
            if node_type == "author":
                if connected_institutions:
                    st.sidebar.markdown("**Institutions:**")
                    for inst in connected_institutions: st.sidebar.markdown(f"- {inst}")
                if connected_funders:
                    st.sidebar.markdown("**Funders (Potential Conflicts):**")
                    for fund in connected_funders: st.sidebar.markdown(f"- {fund}")
            
            elif node_type == "institution":
                if connected_authors:
                    st.sidebar.markdown("**Authors:**")
                    for auth in connected_authors: st.sidebar.markdown(f"- {auth}")
                # Institutions can also be connected to funders directly in some models,
                # but current graph only links authors to institutions/funders.
                # If institutions were linked to funders, that logic would go here.
            
            elif node_type == "funder":
                if connected_authors:
                    st.sidebar.markdown("**Funded Authors:**")
                    for auth in connected_authors: st.sidebar.markdown(f"- {auth}")
            
            if not (connected_authors or connected_institutions or connected_funders):
                st.sidebar.markdown("No direct connections in the current view (or it's an isolated node).")
        else:
             st.sidebar.markdown("Node details not available in the current subgraph view (node might have been filtered out if it wasn't a direct match or neighbor).")

    else: # Multiple nodes matched (by search string, not necessarily direct selection)
        st.sidebar.write(f"{len(filtered_nodes_info)} nodes' names contained '{search_query}'. Displaying their subgraph.")
        with st.sidebar.expander("List of Matched Nodes", expanded=False):
            for node_name, node_type in filtered_nodes_info:
                st.markdown(f"- **{node_name}** ({node_type.capitalize()})")
elif search_query and not filtered_nodes_info:
    st.sidebar.info("No nodes found matching your query.")


# Visualize the graph (either full or subgraph)
# The key for st.pyplot ensures it redraws when the figure object changes or after data addition.
# Using a combination of search_query and a counter that increments on data addition
# could be more robust for cache invalidation and re-plotting.
# For now, st.experimental_rerun() after clearing cache should handle redraw.
fig = visualize_network(display_graph)
st.pyplot(fig, key=f"graph_display_{search_query}_{doi_input}") # Dynamic key based on inputs

# Some debugging print statements removed for clarity (e.g., author-funder print)
