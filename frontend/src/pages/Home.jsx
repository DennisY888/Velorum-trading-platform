import { useState, useEffect } from "react";
import api from "../api";
import Note from "../components/Note"
import "../styles/Home.css"


function Home() {

    const [notes, setNotes] = useState([]); // all the notes we currently have from backend
    const [content, setContent] = useState(""); // content of my new created note
    const [title, setTitle] = useState(""); // title of my new created note

    useEffect(() => {
        getNotes();
    }, []);

    const getNotes = () => {
        api.get("/api/notes/")
            .then((res) => res.data)
            .then((data) => {
                setNotes(data);
                console.log(data);
            })
            .catch((err) => alert(err));
    };


    const deleteNote = (id) => {
        api.delete(`/api/notes/delete/${id}/`)
            .then((res) => {
                if (res.status === 204) alert("Note deleted!");
                else alert("Failed to delete note.");
                // instead of removing the single note from our state, we just refetch all the notes and set a new state (NOT optimal)
                getNotes();
            })
            .catch((error) => alert(error));
    };


    const createNote = (e) => {
        // prevent default submission and add custom submission logic
        e.preventDefault();

        api.post("/api/notes/", { content, title })
            .then((res) => {
                
                if (res.status === 201) alert("Note created!");
                else alert("Failed to make note.");
                
                // insetead of adding the single note from our state, we just refetch all the notes and set a new state (NOT optimal)
                getNotes();
            })
            .catch((err) => alert(err));
    };




    return (
        <div>
            <div>
                <h2>Notes</h2>
                {/* the key attribute passed into the component is just convention, just like for list items */}
                {notes.map((note) => (
                    <Note note={note} onDelete={deleteNote} key={note.id} />
                ))}
            </div>


            <h2>Create a Note</h2>
            <form onSubmit={createNote}>

                <label htmlFor="title">Title:</label>
                <br />
                <input
                    type="text"
                    id="title"
                    name="title"
                    required
                    onChange={(e) => setTitle(e.target.value)}
                    value={title}
                />


                <label htmlFor="content">Content:</label>
                <br />
                <textarea
                    id="content"
                    name="content"
                    required
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                ></textarea>
                <br />

                <input type="submit" value="Submit"></input>
            </form>
        </div>
    );
}

export default Home