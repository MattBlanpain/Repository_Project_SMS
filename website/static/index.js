function deleteNote(noteId) {
    fetch("/delete-note", {
      method: "POST",
      body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
      window.location.href = "/";
    });
  }

  function createSkill(new_skill_name) {
    fetch("/create-skill", {
      method: "POST",
      body: new_skill_name,
    }).then((_res) => {
      window.location.href = "/";
    });
  }